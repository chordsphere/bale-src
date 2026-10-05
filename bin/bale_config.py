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

The one sibling imported at module top is `bale_wizard`, the shared
wizard presentation layer section 3 draws through: it is a stdlib-only
leaf that imports nothing from `bin/`, so it carries no circular-import
hazard to sidestep.

Sections:
  1. Imports + constants                              (~line   85)
  2. Configurables: load and merge                    (~line  460)
  3. `bale config init` wizard                        (~line 1885)
     (its detected-defaults block, the alternatives each screen
     offers, starts ~line 1990)
  4. `bale config hooks` — the acceptance store view  (~line 4465)

Constants exported for `bin/bale`'s use (referenced by `run_hook` for
layer detection, and by `build_parser` for command dispatch):
  - GLOBAL_USER_DIR — absolute path to <install>/user/, the user-owned
    subtree where global config and global hook scripts live.
  - HOOK_ACCEPTANCES_NAME / HOOK_ACCEPTANCES_PATH — the acceptance
    store's file name and absolute path (section 2's store trio).
  - cmd_config_init — argparse-bound entry point for `bale config init`.
  - cmd_config_hooks — argparse-bound entry point for `bale config
    hooks` (v0.4.29, board 83; section 4).

Sections are [hooks], [apply], [staging], [identity], [probe] (both
layers) and [validation], [sandbox], [pack], [layout] (project layer
only); each section's tuple below documents its keys and its layer
ruling. ([probe] joined the both-layer set with session wizard-defaults:
the clipboard command is per-machine, see PROBE_VALUES.)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, NamedTuple, Optional, Sequence

# TOML parsing goes through the in-tree shim rather than stdlib `tomllib`
# directly: `tomllib` is stdlib only on Python 3.11+, and bale supports 3.10
# (which has no stdlib TOML parser). `_bale_toml` exposes the same
# load/loads/TOMLDecodeError surface, backed by stdlib `tomllib` on 3.11+ and a
# vendored pure-Python parser on 3.10. Imported by bare name because `bin/` is
# on sys.path (bin/bale prepends it; see this module's top docstring). Aliased
# to `tomllib` so the call sites below read as ordinary tomllib usage.
import _bale_toml as tomllib

# The shared wizard presentation layer (section 3 draws through it). A
# stdlib-only leaf sibling that imports nothing from bin/, so — unlike
# bin/bale's helpers, which this module pulls lazily from __main__ — it is
# safe to import at module top by bare name, for the same sys.path reason
# as _bale_toml above.
import bale_wizard


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
# The hook acceptance store (v0.4.27, board 78): the install's memory of
# which project-layer / configured hook scripts the operator has accepted
# at the confirmation prompt, by the sha256 of the script's bytes. Lives
# beside the global config under <install>/user/ — user-owned, never
# committed, and its absence reads as "nothing accepted yet". See
# HOOK_ACCEPTANCES_NAME's accessor trio below.
HOOK_ACCEPTANCES_NAME = "hook-acceptances.json"
HOOK_ACCEPTANCES_PATH = GLOBAL_USER_DIR / HOOK_ACCEPTANCES_NAME

# Hooks bale knows how to invoke. Sessions adding a new hook extend this
# tuple AND walk_configurables() (with its WIZARD_WALK_ORDER_* entry) AND
# render_bale_toml() in the same
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
    # String: repo-relative directory of the project's response-archive
    # convention (BALE.md §13's v0.5 candidate, landed). When set, the
    # apply pipeline's applied outcome — after the merge succeeds, and
    # only then — copies whichever of the response's prose artifacts
    # (README.md, notes.md, plus a legacy next-prompt.md) the response
    # actually included into <archive_dir>/<sid>/ as untracked
    # working-tree files; committing them stays the operator's job.
    # Absent/empty = no archival (today's behavior, byte-identical).
    # Repo-relative only: the copies are working-tree writes, so an
    # absolute or repo-escaping value is a typo or interference — the
    # typed accessor refuses both loudly.
    "archive_dir",
    # Bool. Config-gated auto-sweep commits of bale-written bookkeeping
    # (v0.3.32; BALE.md §8.8): when true, the closure-shaped events —
    # apply's terminal outcomes, unlock, revert, rollback/undo, and
    # pack's session closes — stage exactly the telemetry record(s)
    # written this invocation plus the archive_dir copies made this
    # invocation, and commit them as `[bale sweep <sid>] <event>`.
    # Never a directory glob, never `git add -A`; degenerate git states
    # (in-progress merge, detached HEAD, no committable identity) skip
    # loudly and leave the files for a manual sweep. Absent/false =
    # today's behavior byte-identically: bale writes the files
    # untracked and never commits.
    "sweep",
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

# Value-shaped configurables under the [validation] section — the blind-
# checkpoint surface (board 6 session A). Same trio contract as
# APPLY_VALUES / STAGING_VALUES / IDENTITY_VALUES: each key has a typed
# accessor, a walk_configurables() block, and a render_bale_toml() branch.
# Unlike every section above, [validation] is PROJECT-LAYER ONLY at v1
# (ratified 2026-08-04, disposition 1): the wizard walks it in project
# mode only, and merged_config never inherits it from the global layer.
# The rationale, from the ratification: the checkpoint script must be
# committed per-repo regardless (the dangling rule), so a global key
# never saves more than one config line — while adding a dual-resolution
# rule under which the same global key silently names a different oracle
# in every repo it touches, including repos where a file happens to sit
# at the conventional path without the planner ever having ratified it.
# Oracle-by-coincidence is a worse failure than one line of per-repo
# config. The layered form (project overrides global per-key, "" to
# suppress) is the recorded deferred widening; it must answer
# oracle-by-coincidence before it lands.
VALIDATION_VALUES = (
    # String: repo-relative path of the planner-authored blind checkpoint
    # script, committed at the project's tree. Executed by `bale apply`
    # from the BASE TREE's bytes (git show <base_sha>:<path>) — never the
    # staged overlay — before the worker's validation.sh (BALE.md §8.5).
    # Absent/empty = no blind checkpoint (today's behavior). Configured
    # but absent at the base tree = loud refusal at apply. The value may
    # contain the literal token {sid} (v0.4.8, board 10 S7), resolved
    # with the session id at pack time and everywhere downstream via
    # resolve_checkpoint_path — per-session checkpoints; a value without
    # the token behaves byte-for-byte as before. Any other {token} is
    # refused at config read (get_validation_base). The wizard offers
    # both conventions by number (validation_base_alternatives): the
    # per-session <agent_dir>/checkpoints/{sid}.sh and the shared
    # scripts/validation.base.sh.
    "base",
    # Flat list of check names (board 6 session B): the project's
    # REQUIRED validation checks. When non-empty, apply's pre-flight
    # step 15 (BALE.md §8.1) requires every name to appear verbatim in
    # the response manifest's validation_will_run whenever changes[] is
    # non-empty — the superset rule that converts the declaration floor
    # to contract. Whole-project at v1: no file-type or path keying
    # (the keyed-table shape is the same wizard-unwalkable structure
    # the [validation] base decision rejected). A declared check may
    # still [SKIP] with a reason at runtime (TARBALL.md §7.2), which is
    # honest and visible; the rule is about declaration, not forced
    # work. Absent/empty = no required set (today's behavior).
    "required",
)

# Value-shaped configurables under the [sandbox] section — the ADR-0016
# position-3 network grant (v0.4.5, board 10 S2). Same trio contract as
# the sections above: each key has a typed accessor, a
# walk_configurables() block, and a render_bale_toml() branch. Like
# [validation], the section is PROJECT-LAYER ONLY: the grant is
# planner-granted, per-project, and contract-only (ADR-0016: it lives
# in planner-controlled project configuration, decided when the project
# adopts the workflow shape, "never global" per the ratified decision) —
# the wizard walks it in project mode only, and merged_config never
# inherits it from the global layer, so a hand-edited global key cannot
# silently grant network to every repo the install touches.
SANDBOX_VALUES = (
    # Bool. When true, bale passes network=True to every confined
    # response-script execution in this repo — apply.sh, the blind
    # checkpoint, validation.sh — so the sandbox's unshare invocation
    # omits --net (bale_sandbox.confined_command). The confinement
    # floor is unchanged: absent/false = network off (run_confined's
    # own default stays --net), and the grant relaxes the network leg
    # only — filesystem confinement and environment scrubbing are
    # identical either way. Never worker-granted: nothing in a
    # response tarball can request, declare, or widen it; the key
    # lives in committed project config and is never prompted at
    # runtime. Every apply that runs confined scripts with the grant
    # active logs it and stamps network_grant_exercised: true into
    # the attempt's telemetry record (BALE.md §8.9).
    "network",
    # Bool, default true. When false (v0.4.26, board 75), every
    # response-script execution bale would confine in this repo —
    # apply.sh, the blind checkpoint, validation.sh, and `bale open`'s
    # checkpoint dry-run — runs UNCONFINED, exactly as a per-invocation
    # --no-sandbox does: operator privileges, inherited environment,
    # network on. The durable form of the escape, for hosts that lack
    # unprivileged user namespaces (an operator's work server) and
    # would otherwise need --no-sandbox typed on every apply. The
    # posture is convenient, never invisible: every run it disables
    # emits a FORCE-class line naming this key as the source, and the
    # attempt's telemetry record stamps sandbox_confined: false with
    # sandbox_off_source: "config" (BALE.md §8.5, §8.9). Project layer
    # only, like `network`: a global `enabled = false` is ignored, so a
    # hand-edited global key cannot silently unconfine every repo the
    # install touches. Absent/true = confined (today's behavior); a
    # non-bool is fatal, never a silent default (get_sandbox_enabled).
    "enabled",
)

# Value-shaped configurables under the [pack] section — the named
# include/forecast group (board 64). Same trio contract as the sections
# above: each key has a typed accessor (get_pack_include_group reads
# all three as one validated unit), a walk_configurables() block, and a
# render_bale_toml() branch. Like [validation] and [sandbox], the
# section is PROJECT-LAYER ONLY: an include group names paths that
# exist in ONE repo's tree (bale-src's release surface is bale-src's),
# and a global group would engage in every repo the install touches and
# refuse loudly wherever its pulls dangle — the same every-repo hazard
# the [validation] project-only ruling rejected. merged_config never
# inherits [pack] from the global layer, and the global wizard never
# walks it.
#
# One group per project at v1, spelled as three flat keys rather than a
# keyed sub-table — the keyed-table shape is the same wizard-unwalkable
# structure the [validation].required decision rejected. A multi-group
# form is the recorded deferred widening; it needs a wizard-walkable
# spelling before it lands.
PACK_VALUES = (
    # String: the group's name — the spelling users see in config, in
    # the `--no-include-group NAME` opt-out flag, in pack's report
    # lines, and in BALE.md (§7.2). Absent/empty = no group configured
    # (today's behavior). Setting the name requires both list keys
    # below to be non-empty — a half-configured group is fatal at read,
    # never a silent no-op.
    "include_group",
    # List of repo-relative trigger paths. The group engages when the
    # pack's resolved include set intersects any entry (directory
    # entries cover their subtrees, `.` covers everything — the
    # scope_paths_intersect relation). Read-side only: engagement never
    # touches the write forecast.
    "include_group_triggers",
    # List of repo-relative paths the engaged group pulls into the
    # pack's shipped context (and manifest.context_included). Each
    # pulled entry must exist at engagement time; a dangling entry is a
    # loud pack refusal (config rot must not silently thin the shipped
    # context the group exists to guarantee).
    "include_group_pulls",
)

# Value-shaped configurables under the [probe] section — this machine's
# clipboard command (registry fold-in, ratified 2026-08-18,
# configurable-never-core; the config-side carrier landed with board
# 99a). Same trio contract as the sections above: a typed accessor
# (get_probe_clipboard_command, plus effective_clipboard_command for
# bale code), a walk_configurables() block, and a render_bale_toml()
# branch.
#
# BOTH LAYERS since session wizard-defaults (friction-points arc, wave
# 2, ruling 1 answered "as assumed"): the command is a property of the
# machine, so it is set once in the global file and a project may
# override it, or suppress it with "" — per-key replacement, exactly as
# [identity] packer layers. That reverses the earlier project-only
# ruling, whose reason was reach: the key's first consumer,
# tools/craft_response.py --probe, reads `[probe] clipboard_command`
# with its own stdlib-only scan (read_clipboard_command) from the
# project file as shipped in a request, and never sees the global file.
# The reversal rests on bale doing the copy itself, which landed in
# session clipboard-paste-blocks (D, wave 3): every paste block bale
# prints is copied through effective_clipboard_command, and the probe
# scaffold copies through the installed bale (`bale clipboard`), so a
# global value reaches probes too. The crafter still reads the project
# file at craft time, for one fallback only (a machine with no bale on
# PATH) — which is why the key keeps its spelling: a project bale.toml
# that sets it is still read by the crafter after any `bale config
# init` re-run, with no migration and no alias.
PROBE_VALUES = (
    # String: the shell command that copies its stdin to the clipboard
    # (e.g. "pbcopy", "xclip -selection clipboard", "clip.exe"). Absent
    # or empty = no clipboard copy; the probe scaffold carries remedy
    # text walking the operator through this opt-in instead. The value
    # must stay inside the crafter scan's readable shape — one line, no
    # backslash, no double quote, no control characters — so the
    # accessor and the wizard refuse anything the crafter would
    # silently read as unset (probe_clipboard_command_problem); and the
    # line itself must be spelled the way the scan reads it — a one-line
    # basic or literal string under a [probe] header, never
    # triple-quoted (clipboard_command_spelling_problem).
    "clipboard_command",
)

# The named clipboard commands `bale config init` offers on the
# probe.clipboard_command screen, always, whatever the machine: (value,
# aside). Detection (detect_clipboard_command) marks one as detected and
# moves it to [1]; it never sets anything.
CLIPBOARD_ALTERNATIVES = (
    ("pbcopy", "macOS"),
    ("clip.exe", "Windows and WSL"),
    ("wl-copy", "Wayland"),
    ("xclip -selection clipboard", "X11"),
    ("xsel --clipboard --input", "X11"),
)

# Value-shaped configurables under the [layout] section — where the
# project keeps the agent-facing tree bale reads from and writes to
# (v0.4.42, the 100 arc's W2). Same trio contract as the sections
# above: a typed accessor (get_layout_agent_dir), a walk_configurables()
# block, and a render_bale_toml() branch. PROJECT-LAYER ONLY, for the
# reason [validation] is: the value names a directory of THIS repo's
# tree, and a global default would silently reroute every repo's
# telemetry the moment one operator set it. The default is the
# directory every existing repo already uses, so an absent key renames
# nothing.
LAYOUT_VALUES = (
    # String: the repo-relative directory that holds the agent-facing
    # tree — today the telemetry home, `<agent_dir>/telemetry/` (BALE.md
    # §8.9). Absent or empty = DEFAULT_AGENT_DIR. One repo-relative
    # path, no `..` component, never absolute (layout_agent_dir_problem).
    # Only project paths read it; bale-src's own claude/changelog/ and
    # claude/context/ are source paths of this repository, not of the
    # project a bale install serves, and stay where they are.
    "agent_dir",
)

# The directory name every repo used before the key existed, and what an
# unset key still means. Changing this constant renames every unconfigured
# repo's telemetry home at once, so it is the one value here that is not a
# default in the "reasonable starting point" sense: it is history.
DEFAULT_AGENT_DIR = "claude"


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

def read_config_file(path: Path) -> tuple[dict, Optional[str]]:
    """(parsed, refusal) for one bale.toml layer file — never exits.

    ({}, None) when the file is absent; (dict, None) when it parses;
    ({}, "<why>") when it is malformed or unreadable, the refusal worded
    exactly as load_config / load_global_config's fail() words it. The
    one implementation of both loaders (session log-hold): they fail() on the
    refusal, and clipboard_command_reading returns it as a value, so a
    reader that must not end the command reads the same bytes the same
    way."""
    if not path.is_file():
        return {}, None
    try:
        with path.open("rb") as f:
            return tomllib.load(f), None
    except tomllib.TOMLDecodeError as e:
        return {}, f"{path} is malformed TOML: {e}"
    except OSError as e:
        return {}, f"could not read {path}: {e}"


def load_config(repo: Path) -> dict:
    """Return parsed <repo>/bale.toml as a dict, or {} if the file is absent.

    Project layer only — for the layered effective config, use merged_config().

    A missing file is the canonical opt-out — the project's behavior collapses
    to no-config (or, in the layered model, to whatever the global layer
    supplies). A malformed file is fatal: we never want a typo to silently
    disable a configured hook the user thought was wired up.
    """
    from __main__ import fail

    cfg, refusal = read_config_file(repo / BALE_CONFIG)
    if refusal is not None:
        fail(refusal)
    return cfg


def load_global_config() -> dict:
    """Return parsed <install>/user/bale.toml as a dict, or {} if absent.

    Global layer only — for the layered effective config, use merged_config().

    Same contract as load_config: absent = silent {}, malformed = fatal. The
    file lives inside the install so the install dir stays portable as a unit;
    `bale config init --global` is the canonical writer.
    """
    from __main__ import fail

    cfg, refusal = read_config_file(GLOBAL_CONFIG_PATH)
    if refusal is not None:
        fail(refusal)
    return cfg


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

    # [validation] — PROJECT LAYER ONLY (ratified disposition 1; see
    # VALIDATION_VALUES). Deliberately no `elif key in g_validation`
    # branch: a [validation] table in the global file is ignored here,
    # never inherited, so a hand-edited global key cannot silently name
    # a different oracle in every repo (oracle-by-coincidence). The
    # layered form is the recorded deferred widening.
    p_validation = (p.get("validation")
                    if isinstance(p.get("validation"), dict) else {})
    out_validation: dict = {}
    for key in VALIDATION_VALUES:
        if key in p_validation:
            out_validation[key] = p_validation[key]
    if out_validation:
        merged["validation"] = out_validation

    # [sandbox] — PROJECT LAYER ONLY (v0.4.5, board 10 S2; see
    # SANDBOX_VALUES). Deliberately no `elif key in g_sandbox` branch:
    # a [sandbox] table in the global file is ignored here, never
    # inherited — the ADR-0016 network grant is planner-granted and
    # per-project ("never global"), and a global key would silently
    # widen network to every repo the install touches, the same
    # every-repo hazard the [validation] project-only ruling rejected.
    p_sandbox = (p.get("sandbox")
                 if isinstance(p.get("sandbox"), dict) else {})
    out_sandbox: dict = {}
    for key in SANDBOX_VALUES:
        if key in p_sandbox:
            out_sandbox[key] = p_sandbox[key]
    if out_sandbox:
        merged["sandbox"] = out_sandbox

    # [pack] — PROJECT LAYER ONLY (board 64; see PACK_VALUES).
    # Deliberately no `elif key in g_pack` branch: an include group
    # names one repo's tree, and a global group would engage in every
    # repo the install touches — the same every-repo hazard the
    # [validation] and [sandbox] project-only rulings rejected. A
    # hand-edited global [pack] table is ignored here, never inherited.
    p_pack = (p.get("pack")
              if isinstance(p.get("pack"), dict) else {})
    out_pack: dict = {}
    for key in PACK_VALUES:
        if key in p_pack:
            out_pack[key] = p_pack[key]
    if out_pack:
        merged["pack"] = out_pack

    # [probe] — both layers since session wizard-defaults (see
    # PROBE_VALUES): the same per-key replacement as [identity]. A key
    # set at the project layer wins; absent inherits global; the
    # empty-string form passes through and reads as "unset" in the
    # typed accessor, giving the project layer its suppress form.
    g_probe = g.get("probe") if isinstance(g.get("probe"), dict) else {}
    p_probe = p.get("probe") if isinstance(p.get("probe"), dict) else {}
    out_probe: dict = {}
    for key in PROBE_VALUES:
        if key in p_probe:
            out_probe[key] = p_probe[key]
        elif key in g_probe:
            out_probe[key] = g_probe[key]
    if out_probe:
        merged["probe"] = out_probe

    # [layout] — PROJECT LAYER ONLY (v0.4.42; see LAYOUT_VALUES). No
    # `elif key in g_layout` branch: the key names a directory of one
    # repo's tree, and a global value would reroute every repo's
    # telemetry home at once. A hand-edited global [layout] is ignored
    # here, never inherited.
    p_layout = (p.get("layout")
                if isinstance(p.get("layout"), dict) else {})
    out_layout: dict = {}
    for key in LAYOUT_VALUES:
        if key in p_layout:
            out_layout[key] = p_layout[key]
    if out_layout:
        merged["layout"] = out_layout

    return merged


# ---------------------------------------------------------------------------
# Hook acceptance store (v0.4.27, board 78)
# ---------------------------------------------------------------------------
#
# Trust by layer, then by bytes. A global-layer hook (under <install>/user/)
# is the operator's own script and defaults accept at the prompt. A
# project-layer or `configured` (neither-layer) hook defaults decline
# until the operator has accepted that exact script — identified by the
# sha256 of its bytes — once; the acceptance is remembered here, and
# thereafter that script defaults accept. Changed bytes are a new key and
# ask again with the decline default. This is trust-on-first-accept: a
# cloned repo's committed hook can never ride a default (board 45's
# threat model), and the operator's own post_apply_pass stops asking
# after one look. The store is a prompt DEFAULT, never a bypass:
# --no-interact and apply.hook_auto_accept keep their exact semantics,
# and neither writes here — a bypassed prompt is not an operator reading
# the bytes, so it earns no memory.
#
# File shape (JSON object, keyed by sha256 hex; every value an object):
#
#   {
#     "<sha256>": {
#       "script": "/abs/path/as/configured",
#       "hook": "post_apply_pass",
#       "layer": "project",
#       "accepted_at": "2026-09-14T20:05:46+00:00"
#     }
#   }
#
# Path, hook name, layer label and timestamp ride beside the hash so a
# human reading the file can audit what was accepted; the hash alone is
# the identity. An unreadable or malformed store is treated as empty
# with a logged warning (silent skips are bugs) — the worst outcome is
# an extra prompt, never a silent accept.

_ACCEPTANCE_KEYS = ("script", "hook", "layer", "accepted_at")


def hook_script_sha256(script_path: Path) -> str:
    """The identity of a hook script for the acceptance store: sha256 of
    its bytes as they are on disk at prompt time. Raises OSError when
    unreadable; run_hook has already checked the file exists and is
    executable, so a raise here is a real read failure, not a missing
    file."""
    import hashlib
    return hashlib.sha256(Path(script_path).read_bytes()).hexdigest()


def load_hook_acceptances(path: Optional[Path] = None) -> dict:
    """Read the acceptance store. Absent → {} silently (the documented
    "nothing accepted yet" reading). Unreadable or malformed → {} with
    a logged warning naming the file, so an operator who hand-edited it
    learns why every hook is asking again."""
    from __main__ import log  # lazy — see module docstring
    store = HOOK_ACCEPTANCES_PATH if path is None else Path(path)
    if not store.is_file():
        return {}
    try:
        data = json.loads(store.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        log(f"hook acceptance store {store} is unreadable or malformed "
            f"({e}); treating it as empty — every project hook will ask "
            f"again until it is fixed or removed")
        return {}
    if not isinstance(data, dict):
        log(f"hook acceptance store {store} is not a JSON object; "
            f"treating it as empty — every project hook will ask again "
            f"until it is fixed or removed")
        return {}
    return data


def hook_previously_accepted(script_sha256: str,
                             path: Optional[Path] = None) -> bool:
    """True when the store remembers an interactive accept of exactly
    these bytes."""
    return script_sha256 in load_hook_acceptances(path)


def record_hook_acceptance(*, script_sha256: str, script_path: Path,
                           hook: str, layer: str,
                           path: Optional[Path] = None) -> Path:
    """Remember an interactive accept of a project/configured hook.
    Rewrites the store atomically (temp file + rename) so a crash mid-
    write leaves the old store intact. Returns the store path. Raises
    OSError on a write failure — the caller logs and continues, since
    the hook the operator just accepted still runs; only the memory is
    lost."""
    from datetime import datetime, timezone
    store = HOOK_ACCEPTANCES_PATH if path is None else Path(path)
    data = load_hook_acceptances(store)
    data[script_sha256] = {
        "script": str(script_path),
        "hook": str(hook),
        "layer": str(layer),
        "accepted_at": datetime.now(timezone.utc).isoformat(
            timespec="seconds"),
    }
    write_hook_acceptances(data, store)
    return store


def write_hook_acceptances(data: dict, path: Optional[Path] = None) -> Path:
    """Rewrite the whole store atomically (temp file + rename) so a crash
    mid-write leaves the old store intact. The one writer both the
    prompt's record path and `bale config hooks --forget` share, so the
    on-disk shape (sorted keys, two-space indent, trailing newline) has
    one home. Creates the user/ dir on first write. Raises OSError."""
    store = HOOK_ACCEPTANCES_PATH if path is None else Path(path)
    store.parent.mkdir(parents=True, exist_ok=True)
    tmp = store.with_name(store.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    os.replace(tmp, store)
    return store


class HookAcceptanceLookupError(LookupError):
    """A sha256-or-prefix did not resolve to exactly one store entry.

    `kind` is "missing" (no entry starts with the prefix) or "ambiguous"
    (more than one does); `matches` carries the full keys that did match,
    so the caller can name them. Raised rather than returned so the two
    refusals cannot be mistaken for an empty result."""

    def __init__(self, kind: str, prefix: str, matches: list[str]):
        self.kind = kind
        self.prefix = prefix
        self.matches = matches
        super().__init__(f"{kind}: {prefix!r} matched {len(matches)} entries")


_SHA256_PREFIX_RE = re.compile(r"^[0-9a-f]{1,64}$")


def resolve_hook_acceptance_key(prefix: str, data: dict) -> str:
    """Resolve a full sha256 or a unique prefix to the store key it names.

    Hex is case-insensitive on input (the store's keys are lowercase
    hexdigests). A string that is not 1–64 hex characters can match
    nothing and raises ValueError, so a typo is refused as a typo rather
    than reported as a missing key. Exactly one match returns the full
    key; zero or several raise HookAcceptanceLookupError."""
    needle = prefix.strip().lower()
    if not _SHA256_PREFIX_RE.match(needle):
        raise ValueError(
            f"{prefix!r} is not a sha256 or a prefix of one (expected 1–64 "
            f"hex characters)")
    matches = sorted(k for k in data if isinstance(k, str)
                     and k.startswith(needle))
    if not matches:
        raise HookAcceptanceLookupError("missing", needle, matches)
    if len(matches) > 1:
        raise HookAcceptanceLookupError("ambiguous", needle, matches)
    return matches[0]


def forget_hook_acceptance(prefix: str,
                           path: Optional[Path] = None) -> tuple[str, dict]:
    """Remove the one entry `prefix` names and rewrite the store.

    Returns (full_key, removed_entry). The removed entry is whatever the
    store held under the key — normally the four documented fields, but
    a hand-edited store's value is returned as found, so what the verb
    reports back is what was actually there. Propagates the resolver's
    ValueError / HookAcceptanceLookupError unchanged, and OSError from
    the write. A malformed store reads as empty here exactly as it does
    for the prompt (load_hook_acceptances logs the warning), so the
    forget then refuses as "missing" beneath that warning."""
    store = HOOK_ACCEPTANCES_PATH if path is None else Path(path)
    data = load_hook_acceptances(store)
    key = resolve_hook_acceptance_key(prefix, data)
    removed = data.pop(key)
    write_hook_acceptances(data, store)
    return key, removed


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


def get_apply_archive_dir(cfg: dict) -> Optional[str]:
    """Return [apply].archive_dir from the merged config, or None if unset.

    Consumed by the apply pipeline's applied outcome (BALE.md §8.8):
    after a successful merge, the response's prose artifacts are copied
    into <archive_dir>/<sid>/. Absent section or absent key returns None
    — no archival, today's behavior. Empty string reads as unset (the
    wizard's suppress form at the project layer — overriding an
    inherited global value with "no archival here").

    A non-string shape is fatal, matching the sibling readers' posture:
    a typo must not silently disable the archival the user thought was
    wired up. So is a value that is absolute or escapes the repo
    (`..` components): the key's contract is untracked working-tree
    writes inside the project (get_validation_base's posture, for the
    same reason — an escaping value is either a typo or interference,
    both loud). Trailing slashes are stripped so the value joins
    cleanly; no tilde or env-var expansion — the committed file names a
    repo-relative literal, portable by construction.
    """
    from __main__ import fail

    apply_section = cfg.get("apply")
    if apply_section is None:
        return None
    if not isinstance(apply_section, dict):
        fail(f"{BALE_CONFIG}: [apply] must be a table, "
             f"got {type(apply_section).__name__}")
    raw = apply_section.get("archive_dir")
    if raw is None:
        return None
    if not isinstance(raw, str):
        fail(f"{BALE_CONFIG}: apply.archive_dir must be a string, "
             f"got {type(raw).__name__}")
    val = raw.strip()
    if not val:
        return None
    # Shape check BEFORE trailing-slash normalization, so "/" is caught
    # as the absolute path it is rather than collapsing to "" (unset).
    if os.path.isabs(val) or ".." in Path(val).parts:
        fail(f"{BALE_CONFIG}: apply.archive_dir must be a repo-relative "
             f"path with no '..' components, got {raw!r}")
    return val.rstrip("/")


def get_apply_sweep(cfg: dict) -> bool:
    """Return [apply].sweep from the merged config; absent → False.

    Consumed by the closure-shaped events (BALE.md §8.8): when True,
    the event's telemetry/archive writes are staged and committed by
    sweep_commit in bin/bale; absent/False leaves them untracked —
    today's behavior, byte-identical. Bool-shaped like no_interact, so
    an explicit `false` at the project layer overrides an inherited
    global `true` (per-key replacement covers it). The strict non-bool
    fatality lives in _get_apply_bool: a typo must not silently flip
    whether bale commits to the operator's repo.
    """
    return bool(_get_apply_bool(cfg, "sweep"))


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


def get_validation_base(cfg: dict) -> Optional[str]:
    """Return [validation].base from the merged config, or None if unset.

    The blind-checkpoint path (board 6 session A; BALE.md §8.5): a
    repo-relative path to the planner-authored checkpoint script,
    committed at the project's tree. Consumed by the apply pipeline,
    which executes the BASE TREE's bytes at that path — never the staged
    overlay — before the worker's validation.sh.

    Merged-config note: [validation] is project-layer only at v1
    (ratified disposition 1) — merged_config never carries a global
    value into this section, so this accessor reads the project's own
    key or nothing.

    Empty string reads as unset (the wizard's skip form; with no global
    inheritance there is nothing to suppress, but the shape stays
    consistent with the sibling accessors). A non-string shape is fatal,
    matching the sibling readers' posture: a typo must not silently
    disable the oracle the planner thought was pinned. So is a path
    that is absolute or escapes the repo (`..` components): the key's
    contract is a repo-relative committed script, and an escaping value
    is either a typo or interference — both loud.
    """
    from __main__ import fail

    validation_section = cfg.get("validation")
    if validation_section is None:
        return None
    if not isinstance(validation_section, dict):
        fail(f"{BALE_CONFIG}: [validation] must be a table, "
             f"got {type(validation_section).__name__}")
    raw = validation_section.get("base")
    if raw is None:
        return None
    if not isinstance(raw, str):
        fail(f"{BALE_CONFIG}: validation.base must be a string, "
             f"got {type(raw).__name__}")
    val = raw.strip()
    if not val:
        return None
    if os.path.isabs(val) or ".." in Path(val).parts:
        fail(f"{BALE_CONFIG}: validation.base must be a repo-relative "
             f"path with no '..' components, got {val!r}")
    # Brace-token validation (v0.4.8, board 10 S7): the one recognized
    # placeholder is the literal {sid} (resolve_checkpoint_path below).
    # Any other well-formed {token} is refused HERE, at config read —
    # which fires at pack, apply, dry-run, and every other reader — so
    # an unrecognized token (a {date} typo, a {SID} case slip) is loud
    # everywhere rather than silently passing through as a literal path
    # that dangles forever. Braces that do not form a {token} pass
    # through as literal path characters, so no half-substitution is
    # possible by construction: resolve_checkpoint_path replaces the
    # exact literal {sid} and nothing else.
    unknown = [t for t in re.findall(r"\{([^{}]*)\}", val) if t != "sid"]
    if unknown:
        rendered = ", ".join(f"{{{t}}}" for t in unknown)
        fail(f"{BALE_CONFIG}: validation.base contains unrecognized "
             f"placeholder token(s) {rendered} in {val!r}; the only "
             f"recognized token is {{sid}} (per-session checkpoint "
             f"resolution, BALE.md \u00a78.5). Fix the token or remove it.")
    return val


def resolve_checkpoint_path(base: str, sid: str) -> str:
    """Resolve a [validation] base value against a session id.

    Pure string resolution, no filesystem access — existence checking
    is the pack gate's job at its call site (v0.4.8, board 10 S7). A
    literal path returns unchanged, byte-for-byte; a value containing
    the literal token {sid} has every occurrence substituted with
    `sid`, giving each session its own checkpoint file instead of the
    shared oracle the pre-S7 single-path model forced. Internal
    callers (pack's provenance stamp, apply's execution and stamp
    verification, the dry-run prediction) route through this function
    so "resolved path" means one thing everywhere.

    Unknown brace tokens never reach here: get_validation_base refuses
    them at config read, so this function's substitution is total —
    no silent half-substitution is possible.
    """
    return base.replace("{sid}", sid)


def get_validation_required(cfg: dict) -> list[str]:
    """Return [validation].required from the merged config; absent or
    empty → [] (no required set — apply's step-15 gate stays out of the
    way, today's behavior).

    The required-check set (board 6 session B; BALE.md §8.1 step 15): a
    flat, whole-project list of check names the response manifest's
    validation_will_run must include verbatim whenever changes[] is
    non-empty. Consumed by the apply pipeline's superset gate.

    Merged-config note: [validation] is project-layer only at v1
    (ratified disposition 1) — merged_config never carries a global
    value into this section, so this accessor reads the project's own
    key or nothing.

    Shape posture mirrors get_staging_untracked_inputs: a non-list
    value, a non-string entry, or an empty-string entry is fatal — a
    typo must not silently weaken the gate the planner thought was
    pinned. Duplicate names are tolerated here (the gate deduplicates);
    order is preserved as configured.
    """
    from __main__ import fail

    validation_section = cfg.get("validation")
    if validation_section is None:
        return []
    if not isinstance(validation_section, dict):
        fail(f"{BALE_CONFIG}: [validation] must be a table, "
             f"got {type(validation_section).__name__}")
    raw = validation_section.get("required")
    if raw is None:
        return []
    if not isinstance(raw, list):
        fail(f"{BALE_CONFIG}: validation.required must be an array "
             f"of check-name strings, got {type(raw).__name__}")
    for i, entry in enumerate(raw):
        if not isinstance(entry, str):
            fail(f"{BALE_CONFIG}: validation.required[{i}] must be a "
                 f"string, got {type(entry).__name__}")
        if not entry.strip():
            fail(f"{BALE_CONFIG}: validation.required[{i}] is empty; "
                 f"remove the entry or name a check")
    return [entry.strip() for entry in raw]


def get_sandbox_network(cfg: dict) -> bool:
    """Return [sandbox].network from the merged config; absent → False.

    The ADR-0016 position-3 network grant (v0.4.5, board 10 S2): when
    True, the apply pipeline passes network=True to every confined
    response-script execution — apply.sh, the blind checkpoint,
    validation.sh — relaxing the sandbox's network leg only. False or
    absent is the confinement floor: network off, byte-identical to
    the pre-grant behavior. The grant gates what bale *passes*; it
    never changes run_confined's own network=False default.

    Merged-config note: [sandbox] is project-layer only (SANDBOX_VALUES
    owns the rationale) — merged_config never carries a global value
    into this section, so this accessor reads the project's own key or
    nothing.

    Bool-shaped like the [apply] bools, so there is no empty-suppress
    form, and the strict non-bool fatality matches _get_apply_bool's
    posture exactly: a typo must not silently grant (or silently
    revoke) network to untrusted script execution — a string "true" is
    a typo in TOML terms, not a boolean.
    """
    from __main__ import fail

    sandbox_section = cfg.get("sandbox")
    if sandbox_section is None:
        return False
    if not isinstance(sandbox_section, dict):
        fail(f"{BALE_CONFIG}: [sandbox] must be a table, "
             f"got {type(sandbox_section).__name__}")
    raw = sandbox_section.get("network")
    if raw is None:
        return False
    if not isinstance(raw, bool):
        fail(f"{BALE_CONFIG}: sandbox.network must be a boolean "
             f"(true/false), got {type(raw).__name__}")
    return raw


def get_sandbox_enabled(cfg: dict) -> bool:
    """Return [sandbox].enabled from the merged config; absent → True.

    The sandbox-off-by-config posture (v0.4.26, board 75). True or
    absent is today's behavior: every response-script execution runs
    confined by default (BALE.md §8.5). False makes the apply pipeline
    (and `bale open`'s checkpoint dry-run) run those scripts UNCONFINED
    exactly as a per-invocation --no-sandbox does — the durable form of
    the escape for namespace-less hosts. Never silent: every run this
    key disables FORCE-logs the key as its source and the telemetry
    record stamps sandbox_confined: false / sandbox_off_source: "config"
    (§8.9). The accessor gates what bale *passes*; run_confined's own
    behavior is untouched.

    Merged-config note: [sandbox] is project-layer only (SANDBOX_VALUES
    owns the rationale) — merged_config never carries a global value
    into this section, so a global `enabled = false` is ignored exactly
    as a global `network` is, and this accessor reads the project's
    own key or nothing.

    Bool-shaped like `network`, with the same strict non-bool
    fatality: a typo must not silently unconfine (or silently confine)
    untrusted script execution — a string "false" is a typo in TOML
    terms, not a boolean.
    """
    from __main__ import fail

    sandbox_section = cfg.get("sandbox")
    if sandbox_section is None:
        return True
    if not isinstance(sandbox_section, dict):
        fail(f"{BALE_CONFIG}: [sandbox] must be a table, "
             f"got {type(sandbox_section).__name__}")
    raw = sandbox_section.get("enabled")
    if raw is None:
        return True
    if not isinstance(raw, bool):
        fail(f"{BALE_CONFIG}: sandbox.enabled must be a boolean "
             f"(true/false), got {type(raw).__name__}")
    return raw


def get_pack_include_group(cfg: dict) -> Optional[dict]:
    """Return the project's named include group, or None if unconfigured.

    The [pack] include-group trio (board 64): `include_group` (the
    name), `include_group_triggers`, and `include_group_pulls` read as
    one validated unit — the shape callers consume is
    `{"name": str, "triggers": list[str], "pulls": list[str]}`.
    Consumed by `bale pack`, which engages the group when the resolved
    include set intersects a trigger and pulls the group's paths into
    the shipped context (read side only — the write forecast is never
    touched; BALE.md §7.2).

    Merged-config note: [pack] is project-layer only (PACK_VALUES owns
    the rationale) — merged_config never carries a global value into
    this section, so this accessor reads the project's own keys or
    nothing.

    Shape posture mirrors the sibling accessors: a typo must not
    silently disable (or half-enable) the group the planner thought
    was pinned. An empty-string name reads as unset — the wizard's
    skip form — but ONLY when both list keys are also absent or empty;
    any partially configured combination (a name without both lists, a
    list without the name) is fatal, because a half-configured group
    that silently never engages is exactly the missing-context failure
    the group exists to retire. Entries are repo-relative with no
    `..` components, matching validation.base's path rules; duplicates
    are tolerated (engagement deduplicates), order preserved.
    """
    from __main__ import fail

    pack_section = cfg.get("pack")
    if pack_section is None:
        return None
    if not isinstance(pack_section, dict):
        fail(f"{BALE_CONFIG}: [pack] must be a table, "
             f"got {type(pack_section).__name__}")

    raw_name = pack_section.get("include_group")
    if raw_name is not None and not isinstance(raw_name, str):
        fail(f"{BALE_CONFIG}: pack.include_group must be a string, "
             f"got {type(raw_name).__name__}")
    name = raw_name.strip() if isinstance(raw_name, str) else ""

    def _path_list(key: str) -> list[str]:
        raw = pack_section.get(key)
        if raw is None:
            return []
        if not isinstance(raw, list):
            fail(f"{BALE_CONFIG}: pack.{key} must be an array of "
                 f"repo-relative path strings, got {type(raw).__name__}")
        out: list[str] = []
        for i, entry in enumerate(raw):
            if not isinstance(entry, str):
                fail(f"{BALE_CONFIG}: pack.{key}[{i}] must be a string, "
                     f"got {type(entry).__name__}")
            val = entry.strip()
            if not val:
                fail(f"{BALE_CONFIG}: pack.{key}[{i}] is empty; "
                     f"remove the entry or name a path")
            if os.path.isabs(val) or ".." in Path(val).parts:
                fail(f"{BALE_CONFIG}: pack.{key}[{i}] must be a "
                     f"repo-relative path with no '..' components, "
                     f"got {val!r}")
            out.append(val)
        return out

    triggers = _path_list("include_group_triggers")
    pulls = _path_list("include_group_pulls")

    if not name and not triggers and not pulls:
        return None
    if not (name and triggers and pulls):
        missing = [k for k, v in (("include_group", name),
                                  ("include_group_triggers", triggers),
                                  ("include_group_pulls", pulls))
                   if not v]
        fail(f"{BALE_CONFIG}: [pack] include group is half-configured — "
             f"missing or empty: {', '.join(missing)}. A group needs "
             f"all three keys (include_group, include_group_triggers, "
             f"include_group_pulls) so it cannot silently never engage; "
             f"set the missing key(s) or remove the group entirely.")
    return {"name": name, "triggers": triggers, "pulls": pulls}


def probe_clipboard_command_problem(value: str) -> Optional[str]:
    """Say why `value` is not a usable [probe] clipboard_command, or None.

    The crafter's reader (tools/craft_response.py read_clipboard_command)
    is a deliberately minimal single-key scan of a one-line TOML basic
    string: it treats a value containing a backslash as unset, cannot
    see past an embedded double quote, and never reads a second line.
    render_bale_toml writes the value with json.dumps, which escapes
    control characters into backslash sequences. So a value carrying any
    of those would round-trip through bale's own TOML parser and then be
    silently unset at craft time — the disagreement this check exists
    to refuse up front. Non-ASCII is fine: the renderer writes it
    literally (ensure_ascii=False). Whitespace at either end is not a
    problem; both readers strip it. The empty string is not judged here
    — callers read it as unset.
    """
    if "\\" in value:
        return "contains a backslash"
    if '"' in value:
        return "contains a double quote"
    for ch in value:
        if ord(ch) < 0x20 or ord(ch) == 0x7F:
            return (f"contains a control character (U+{ord(ch):04X}; "
                    f"one line, no tabs)")
    return None


def get_probe_clipboard_command(cfg: dict) -> Optional[str]:
    """Return [probe].clipboard_command from the merged config, or None.

    The config-side carrier of the probe scaffold's opt-in clipboard
    epilogue (PROBE_VALUES). None when the section or key is absent, or
    the value is empty after stripping — the "no clipboard epilogue"
    state. A set value comes back stripped, which is exactly what the
    crafter's scan yields for the same bytes.

    Merged-config note: [probe] layers like [identity] (PROBE_VALUES
    owns the rationale) — given merged_config's output, this returns
    the project's value, else the inherited global one, and None when
    the project suppresses with "". Bale code that wants the effective
    command calls effective_clipboard_command(repo), which also checks
    how the supplying file spells the key; this dict-level accessor
    cannot see spelling.

    Shape posture: a non-table section or a non-string value is fatal,
    as in the sibling string accessors. So is a string the crafter's
    minimal reader cannot read (probe_clipboard_command_problem): the
    crafter would treat it as unset and emit remedy text, so accepting
    it here would leave bale and the crafter disagreeing about whether
    the opt-in is configured. Right or loud, never split.

    The judging is _probe_clipboard_value's (shared with the non-exiting
    clipboard_command_reading); this accessor makes its refusal fatal.
    """
    from __main__ import fail

    value, refusal = _probe_clipboard_value(cfg)
    if refusal is not None:
        fail(refusal)
    return value


def _probe_clipboard_value(cfg: dict) -> tuple[Optional[str], Optional[str]]:
    """(value, refusal) for [probe].clipboard_command in `cfg` — never
    exits. value is get_probe_clipboard_command's answer when the
    config is acceptable (refusal None); otherwise value is None and
    refusal is the message that accessor fails with, word for word."""
    probe_section = cfg.get("probe")
    if probe_section is None:
        return None, None
    if not isinstance(probe_section, dict):
        return None, (f"{BALE_CONFIG}: [probe] must be a table, "
                      f"got {type(probe_section).__name__}")
    raw = probe_section.get("clipboard_command")
    if raw is None:
        return None, None
    if not isinstance(raw, str):
        return None, (f"{BALE_CONFIG}: probe.clipboard_command must be a "
                      f"string, got {type(raw).__name__}")
    val = raw.strip()
    if not val:
        return None, None
    problem = probe_clipboard_command_problem(val)
    if problem is not None:
        return None, (f"{BALE_CONFIG}: probe.clipboard_command {problem}; "
                      f"the probe scaffold's reader (tools/craft_response.py) "
                      f"would treat it as unset. Use a one-line command with "
                      f"no backslashes or double quotes (wrap it in a script "
                      f"if it needs them).")
    return val, None


def _scan_clipboard_line(text: str) -> tuple[str, Optional[str], str]:
    """Read `[probe] clipboard_command` from bale.toml text the way the
    probe scaffold's reader does. Returns (status, value, raw).

    A deliberate twin of tools/craft_response.py's scan_bale_toml_key
    plus one_line_quoted_value (bin/ never imports tools/, so the rule
    is restated here; tests/test_probe_clipboard_config.py pins the two
    against one corpus of lines). status is "set" (value is the
    stripped command), "bad-shape" (the key's line is there but is not
    a one-line basic or literal string — raw is its value text, so a
    caller can say "triple-quoted"), or "unset" (no such line under a
    [probe] header). Only the spelling is judged: the content rules
    (backslash, double quote, control characters) belong to
    probe_clipboard_command_problem, and a value that breaks them reads
    here as bad-shape too, exactly as it does crafter-side.
    """
    section = None
    for line in (raw.strip() for raw in text.splitlines()):
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            continue
        if section != "probe" or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() != "clipboard_command":
            continue
        value = value.strip()
        got = _one_line_quoted_value(value)
        if got is not None:
            return "set", got, value
        return "bad-shape", None, value
    return "unset", None, ""


def _one_line_quoted_value(value: str) -> Optional[str]:
    """The twin of the crafter's one_line_quoted_value: the stripped
    command inside a one-line basic ("...") or literal ('...') string,
    or None when the shape is outside what that reader reads. The first
    matching quote after the opener closes the value (no escapes are
    read), only a trailing `# comment` may follow, and a triple-quoted
    opener closes at once on an empty value — which is how both
    multi-line forms come out unread."""
    if not value or value[0] not in ('"', "'"):
        return None
    quote = value[0]
    closing = value.find(quote, 1)
    if closing < 0:
        return None
    cmd = value[1:closing].strip()
    rest = value[closing + 1:].strip()
    if not cmd or (rest and not rest.startswith("#")):
        return None
    if probe_clipboard_command_problem(cmd) is not None:
        return None
    return cmd


def clipboard_command_spelling_problem(path: Path) -> Optional[str]:
    """Say why `path` spells a set `[probe] clipboard_command` in a form
    the probe scaffold's reader cannot see, or None.

    The rider routed to this session from 005/69: bale's TOML parser
    reads a triple-quoted value ('''pbcopy''' or \"\"\"pbcopy\"\"\") that
    tools/craft_response.py's one-line scan treats as unset — the one
    known split left after board 69. This closes it bale-side by
    refusing the spelling rather than parsing it: the key has one
    spelling, `clipboard_command = "<command>"` (or single-quoted) on
    one line under a `[probe]` header, at both layers, so a line copied
    from the global file into a project file keeps working. Also
    caught, for the same reason: a dotted key (`probe.clipboard_command
    = ...`) or an inline table, which bale parses and the scan never
    finds.

    Call only when the parsed file sets the key to a non-empty string
    (an absent or empty key has no spelling to judge). An unreadable
    file is reported as the problem rather than passed: the loaders
    parsed it a moment ago, so failing to re-read it is worth saying.
    The wizard rewrites the key in the readable spelling on its next
    write (render_bale_toml), so the remedy is one `bale config init`.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return f"could not be re-read to check its spelling ({e})"
    status, _value, raw = _scan_clipboard_line(text)
    if status == "set":
        return None
    if status == "bad-shape":
        if raw.startswith('"""') or raw.startswith("'''"):
            return "is triple-quoted"
        return "is not a one-line quoted string"
    return ("is not written as a clipboard_command = \"...\" line under "
            "a [probe] header (a dotted key or an inline table, for "
            "example)")


def _probe_layers(repo: Optional[Path]) -> tuple[dict, dict]:
    """The raw [probe] tables of the project file (empty when repo is
    None or the file has none) and the global file. Loading goes through
    load_config / load_global_config, so a malformed file is fatal here
    exactly as everywhere else."""
    p = load_config(repo) if repo is not None else {}
    g = load_global_config()
    p_probe = p.get("probe") if isinstance(p.get("probe"), dict) else {}
    g_probe = g.get("probe") if isinstance(g.get("probe"), dict) else {}
    return p_probe, g_probe


def clipboard_command_source(repo: Optional[Path]) -> Optional[str]:
    """"project" or "global" — the layer whose file decides
    probe.clipboard_command under the per-key merge — or None when
    neither file sets the key.

    "project" includes the suppress form (`clipboard_command = ""`): the
    project decided, and decided "none". `repo` None means no project
    is in play (a command run outside a repo), so only the global file
    can decide. The display twin of effective_clipboard_command, for a
    status row that names where the value came from (apply_bool_source
    is the precedent).
    """
    p_probe, g_probe = _probe_layers(repo)
    if "clipboard_command" in p_probe:
        return "project"
    if "clipboard_command" in g_probe:
        return "global"
    return None


def effective_clipboard_command(repo: Optional[Path]) -> Optional[str]:
    """The clipboard command bale should use here, or None for "no copy".

    The accessor bale code calls (session D's paste-block copying
    builds on it): the project's [probe] clipboard_command when the
    project file sets it, else the global file's, with "" at the
    project layer suppressing an inherited value; `repo` None reads the
    global file alone. The value comes back stripped.

    Fatal, never silent, on anything the dict accessor is fatal on (a
    non-string, a backslash, a double quote, a control character), and
    on a supplying file that spells the key in a form the probe
    scaffold's reader cannot see — triple-quoted above all
    (clipboard_command_spelling_problem). Right or loud, never split:
    bale and the crafter never disagree about whether a file configures
    a clipboard command.

    Nothing here detects anything. A command detected by `bale config
    init` is only ever a suggestion on the wizard screen; bale uses a
    command only once it is written to a bale.toml (the registry
    fold-in's "configurable-never-core").

    The fatal form of clipboard_command_reading (session log-hold):
    same reading, same refusal text, same order of checks, with the
    refusal raised through fail(). A caller that must not end the
    command — the paste-block copy, the status row — reads
    clipboard_command_reading instead and gets the refusal as a value.
    """
    from __main__ import fail

    reading = clipboard_command_reading(repo)
    if reading.refusal is not None:
        fail(reading.refusal)
    return reading.command


class ClipboardCommandReading(NamedTuple):
    """What clipboard_command_reading found. `command` is the command
    to run, or None for "no copy"; `source` is the layer whose file
    decides the key — "project" / "global", None when neither sets it
    or a config file could not be parsed (clipboard_command_source's
    values); `refusal` is None, or the text effective_clipboard_command
    would fail() with — and then `command` is None."""
    command: Optional[str]
    source: Optional[str]
    refusal: Optional[str]


def clipboard_command_reading(repo: Optional[Path]) -> ClipboardCommandReading:
    """effective_clipboard_command's answer without the exit (session
    log-hold, landing session D's first rider).

    Reads exactly what the fatal accessor reads, in the same order —
    both layer files (a malformed or unreadable one refuses, project
    first), the deciding layer's value (a non-string, a backslash, a
    double quote, a control character refuses), then that file's
    spelling of the key (triple-quoted, dotted, inline-table refuses) —
    and returns any refusal as a value instead of calling fail(). So
    nothing is printed, nothing is journaled into an open session log,
    and nothing raises SystemExit: bale_report.copy_paste_block turns a
    refusal into its one "NOT copied" notice and the command goes on.
    """
    if repo is not None:
        p, refusal = read_config_file(repo / BALE_CONFIG)
        if refusal is not None:
            return ClipboardCommandReading(None, None, refusal)
    else:
        p = {}
    g, refusal = read_config_file(GLOBAL_CONFIG_PATH)
    if refusal is not None:
        return ClipboardCommandReading(None, None, refusal)
    p_probe = p.get("probe") if isinstance(p.get("probe"), dict) else {}
    g_probe = g.get("probe") if isinstance(g.get("probe"), dict) else {}
    if "clipboard_command" in p_probe:
        cfg, path, source = {"probe": p_probe}, (repo / BALE_CONFIG), "project"
    elif "clipboard_command" in g_probe:
        cfg, path, source = {"probe": g_probe}, GLOBAL_CONFIG_PATH, "global"
    else:
        return ClipboardCommandReading(None, None, None)
    value, refusal = _probe_clipboard_value(cfg)
    if refusal is not None:
        return ClipboardCommandReading(None, source, refusal)
    if value is None:
        return ClipboardCommandReading(None, source, None)
    problem = clipboard_command_spelling_problem(path)
    if problem is not None:
        rerun = ("bale config init --global" if path == GLOBAL_CONFIG_PATH
                 else "bale config init")
        return ClipboardCommandReading(None, source, (
            f"{path}: probe.clipboard_command {problem}. bale reads the "
            f"key only in the one-line spelling the probe scaffold's "
            f"reader (tools/craft_response.py) can see — "
            f'clipboard_command = "<command>" under a [probe] header. '
            f"Re-run `{rerun}` (it rewrites the key that way) or edit "
            f"the line."))
    return ClipboardCommandReading(value, source, None)


def layout_agent_dir_problem(value: str) -> Optional[str]:
    """Say why `value` is not a usable [layout] agent_dir, or None.

    The key's contract is one repo-relative directory: bale joins it
    under the repo root and under a staging copy alike, so an absolute
    path, a `..` component, or a trailing slash that would double up
    in a rendered prefix is refused at config read rather than quietly
    resolving somewhere outside the tree. The empty string is not
    judged here — callers read it as unset (DEFAULT_AGENT_DIR).
    """
    if os.path.isabs(value):
        return "must be a repo-relative path, not absolute"
    parts = Path(value).parts
    if ".." in parts:
        return "must not contain a '..' component"
    if value.endswith("/") or value.endswith(os.sep):
        return "must not end in a slash"
    if any(ch.isspace() for ch in value):
        return "must not contain whitespace"
    return None


def get_layout_agent_dir(cfg: dict) -> str:
    """Return [layout].agent_dir from the merged config, or DEFAULT_AGENT_DIR.

    The one reader of the key's value (LAYOUT_VALUES): the telemetry
    home is `<repo>/<agent_dir>/telemetry/` — bin/bale's `bale stats`
    corpus, bale_report.telemetry_record_path, and bale_rollback's
    dirty-tree carve-out all derive their path from this accessor, so
    a configured repo has one spelling and an unconfigured one keeps
    the spelling it always had. Never None: absent section, absent key,
    or an empty value after stripping all read as the default.

    Merged-config note: [layout] is project-layer only (LAYOUT_VALUES
    owns the rationale) — merged_config never carries a global value
    into this section, so this accessor reads the project's own key or
    the default.

    Shape posture: a non-table section, a non-string value, or a path
    that escapes the repo (layout_agent_dir_problem) is fatal, as in
    the sibling string accessors — a typo must not silently move the
    telemetry corpus.
    """
    from __main__ import fail

    layout_section = cfg.get("layout")
    if layout_section is None:
        return DEFAULT_AGENT_DIR
    if not isinstance(layout_section, dict):
        fail(f"{BALE_CONFIG}: [layout] must be a table, "
             f"got {type(layout_section).__name__}")
    raw = layout_section.get("agent_dir")
    if raw is None:
        return DEFAULT_AGENT_DIR
    if not isinstance(raw, str):
        fail(f"{BALE_CONFIG}: layout.agent_dir must be a string, "
             f"got {type(raw).__name__}")
    val = raw.strip()
    if not val:
        return DEFAULT_AGENT_DIR
    problem = layout_agent_dir_problem(val)
    if problem is not None:
        fail(f"{BALE_CONFIG}: layout.agent_dir {problem}, got {val!r}")
    return val


def layout_agent_dir(repo: Path) -> str:
    """The repo's agent directory name, read from its own bale.toml.

    The path-building convenience over get_layout_agent_dir: callers
    that only need the directory (telemetry_record_path and friends)
    pass the repo and get the name. Reads the PROJECT layer only, which
    is the whole of where [layout] can live, and short-circuits on an
    absent bale.toml without touching the config loader — so a repo
    with no config file, the common case in unit fixtures, resolves to
    DEFAULT_AGENT_DIR without needing bin/bale's `fail` on the process's
    __main__.
    """
    if not (repo / BALE_CONFIG).is_file():
        return DEFAULT_AGENT_DIR
    return get_layout_agent_dir(load_config(repo))


def layout_agent_dir_for_display(repo: Optional[Path]) -> tuple[str, Optional[str]]:
    """The agent directory for text that must never fail: (name, note).

    layout_agent_dir is fatal on a malformed bale.toml or a bad
    agent_dir value, which is right for every path-building caller — a
    typo must not silently move the corpus. Help text is the one reader
    that must render regardless (v0.4.44, board row 124: `bale stats
    --help` names the configured telemetry home), so this variant never
    calls fail(): a missing repo or config reads as the default with
    note None, and an unreadable config or unusable value reads as the
    default with a short note saying so, which the caller prints beside
    it rather than presenting the default as this repo's setting.
    """
    if repo is None or not (repo / BALE_CONFIG).is_file():
        return DEFAULT_AGENT_DIR, None
    try:
        with (repo / BALE_CONFIG).open("rb") as f:
            cfg = tomllib.load(f)
    except (tomllib.TOMLDecodeError, OSError) as e:
        return DEFAULT_AGENT_DIR, f"{BALE_CONFIG} unreadable ({e})"
    section = cfg.get("layout")
    raw = section.get("agent_dir") if isinstance(section, dict) else None
    if section is not None and not isinstance(section, dict):
        return DEFAULT_AGENT_DIR, "[layout] is not a table"
    if raw is None:
        return DEFAULT_AGENT_DIR, None
    if not isinstance(raw, str):
        return DEFAULT_AGENT_DIR, "layout.agent_dir is not a string"
    val = raw.strip()
    if not val:
        return DEFAULT_AGENT_DIR, None
    problem = layout_agent_dir_problem(val)
    if problem is not None:
        return DEFAULT_AGENT_DIR, f"layout.agent_dir {problem}"
    return val, None


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
#
# Presentation vs meaning (session config-wizard-ui, after v0.4.45). How the
# wizard DRAWS — section headings, one item per screen with its n/N
# position and dotted key, the state rows, the Enter-stating prompt, the
# on-demand '?' help, warnings, the pre-write review — is
# bale_wizard's (the shared wizard presentation layer, a stdlib-only leaf
# sibling). What an answer MEANS — Enter keeps, '-' clears, 'x'
# suppresses, the bool spellings, the reject-with-hint checks — stays
# here, in the _prompt_* helpers and walk_configurables, unchanged. The
# walk order is declared once (WIZARD_WALK_ORDER_* below) and is what the
# n/N positions and the section headings are derived from.

# The keys `bale config init` walks, as dotted keys, in prompt order.
# Both-layer keys first, then the project-layer-only sections (the rulings
# recorded on VALIDATION_VALUES, SANDBOX_VALUES, PACK_VALUES, and
# LAYOUT_VALUES). walk_configurables() opens each key's screen through
# bale_wizard.Walk, which refuses a key missing from this tuple, and the
# tests pin that the walk visits exactly these keys in exactly this order —
# so a configurable added to walk_configurables() must be added here too,
# and the "3/19" a user sees cannot drift from the keys actually walked.
WIZARD_WALK_ORDER_BOTH_LAYERS = (
    "hooks.post_pack",
    "hooks.post_apply_pass",
    "apply.search_paths",
    "apply.no_interact",
    "apply.hook_auto_accept",
    "apply.archive_dir",
    "apply.sweep",
    "staging.strategy",
    "staging.untracked_inputs",
    "identity.packer",
    # Both layers since session wizard-defaults (PROBE_VALUES): last of
    # the both-layer keys, so the global walk ends on it and the project
    # walk reaches it before the project-only sections.
    "probe.clipboard_command",
)
WIZARD_WALK_ORDER_PROJECT_ONLY = (
    "validation.base",
    "validation.required",
    "sandbox.network",
    "sandbox.enabled",
    "pack.include_group",
    "pack.include_group_triggers",
    "pack.include_group_pulls",
    "layout.agent_dir",
)

# One heading note per TOML section, shown on the section's heading line.
# Project-layer-only sections say so on the heading, once, rather than in
# every item's summary.
_WIZARD_SECTION_NOTES = {
    "hooks": "scripts bale runs after pack and apply",
    "apply": "inbound files and apply-time behavior",
    "staging": "how apply builds the validation tree",
    "identity": "who authors packs",
    "validation": "blind checkpoint, required checks",
    "sandbox": "confinement of response scripts",
    "pack": "the include group",
    "probe": "this machine's clipboard command",
    "layout": "where the agent-facing tree lives",
}
_PROJECT_ONLY_SECTIONS = ("validation", "sandbox", "pack", "layout")


def wizard_walk_order(layer: str) -> tuple[str, ...]:
    """The dotted keys `bale config init` walks at `layer`, in order."""
    if layer == "project":
        return WIZARD_WALK_ORDER_BOTH_LAYERS + WIZARD_WALK_ORDER_PROJECT_ONLY
    if layer == "global":
        return WIZARD_WALK_ORDER_BOTH_LAYERS
    raise ValueError(f"unknown layer: {layer!r}")


def _wizard_walk(layer: str,
                 ui: Optional[bale_wizard.WizardUI] = None) -> bale_wizard.Walk:
    """A Walk over `layer`'s keys with the section heading notes."""
    notes = {
        section: (f"{note} · project layer only"
                  if section in _PROJECT_ONLY_SECTIONS else note)
        for section, note in _WIZARD_SECTION_NOTES.items()
    }
    return bale_wizard.Walk(ui or bale_wizard.WizardUI(),
                            wizard_walk_order(layer), notes)


# ---- Detected defaults and named alternatives (session wizard-defaults) ---
#
# The friction-points review found that several keys make the operator
# remember a value bale could have offered: the clipboard command, the
# WSL Downloads path, git's user.name, the response-archive and
# checkpoint conventions, the two staging strategies, the untracked
# dependency directories, and .baleignore patterns for what the repo
# actually holds. Each of those screens now lists numbered alternatives
# (bale_wizard.Alternative, drawn by WizardUI.alternatives) and reads its
# answer with WizardUI.ask_choice, where a number takes that value.
#
# Three rules bind everything below:
#   - Detection only suggests. A detected value is listed first and
#     marked "detected"; nothing is set until the operator types its
#     number or the value. Nothing outside the wizard screen reads these
#     functions (the registry fold-in's configurable-never-core).
#   - Enter keeps the meaning it always had on every key (keep current,
#     keep inheriting, leave unset), so an Enter-through run still
#     writes nothing the operator did not choose.
#   - Detection never fails the wizard. Finding nothing degrades to the
#     static alternatives, or to the screen as it was; a detector that
#     could not run (git missing, a timeout) leaves its key without the
#     detected rows and says so in one dim line on that key's screen
#     (WizardSuggestions.notes) rather than skipping silently.
#
# Every detector takes its environment as parameters (platform, environ,
# which, home, the repo) so the tests pin each outcome without touching
# the machine they run on; suggest_wizard_values gathers them for a walk.

# Seconds any one detection subprocess (git) may take before it is
# abandoned. The wizard is interactive; a hung git must not hang it.
DETECTION_TIMEOUT = 5

# Untracked dependency directories offered for staging.untracked_inputs
# when present at the repo root and untracked (a gitignored directory
# counts — that is the usual case).
UNTRACKED_INPUT_CANDIDATES = (".venv", "node_modules")

# Windows profile directories under /mnt/c/Users that are not a person's
# profile; their Downloads (when any) is never offered.
_WINDOWS_NON_PROFILES = frozenset({
    "public", "default", "default user", "all users",
    "defaultapppool", "wdagutilityaccount",
})

# How many Windows-side Downloads directories to offer at most (a shared
# machine can have several profiles; the one matching $USER comes first).
WINDOWS_DOWNLOADS_MAX = 3

# .baleignore suggestion signals (the session's judgment, recorded in its
# notes): bulky or binary formats a request tarball rarely needs, by
# extension; directory names that usually hold data or vendored code;
# and any single shippable file at least BALEIGNORE_LARGE_FILE_BYTES
# that neither rule covers. Only what pack would ship is counted —
# tracked plus untracked-not-ignored files (git ls-files, as pack lists
# them), outside pack's baked-in excluded directories.
BALEIGNORE_SUGGEST_EXTENSIONS = frozenset({
    # data and serialized models
    "parquet", "feather", "arrow", "avro", "orc", "h5", "hdf5", "npy",
    "npz", "pkl", "pickle", "joblib", "sqlite", "sqlite3", "db", "duckdb",
    "onnx", "pt", "pth", "ckpt", "safetensors",
    # archives and packages
    "zip", "tar", "gz", "tgz", "bz2", "xz", "7z", "rar", "jar", "war",
    "whl", "egg", "iso", "dmg",
    # media
    "mp4", "mov", "avi", "mkv", "wav", "mp3", "flac",
    # compiled
    "exe", "dll", "so", "dylib",
})
BALEIGNORE_SUGGEST_DIRS = ("data", "datasets", "vendor", "third_party",
                           ".idea", ".vscode")
BALEIGNORE_LARGE_FILE_BYTES = 1024 * 1024
BALEIGNORE_SUGGESTIONS_MAX = 6


@dataclass
class WizardSuggestions:
    """What one `bale config init` walk offers beside its prompts.

    `alternatives` maps a dotted key to its offered values (in any
    order; `for_key` puts the detected ones first, which is the order
    the screen numbers). `notes` are dim informational lines for a key's
    screen (a detector that could not run); `warnings` are reject-style
    lines (the file spells the key in a form a reader cannot see). An
    empty WizardSuggestions draws every screen exactly as it was before
    alternatives existed — which is what the tests pass when they mean
    "no detection".
    """
    alternatives: dict = field(default_factory=dict)
    notes: dict = field(default_factory=dict)
    warnings: dict = field(default_factory=dict)

    def for_key(self, key: str) -> list:
        return bale_wizard.detected_first(self.alternatives.get(key, ()))

    def note(self, key: str, text: str) -> None:
        self.notes.setdefault(key, []).append(text)

    def warn(self, key: str, text: str) -> None:
        self.warnings.setdefault(key, []).append(text)


def is_wsl(environ: Optional[dict] = None,
           osrelease: Path = Path("/proc/sys/kernel/osrelease")) -> bool:
    """Whether this looks like Windows Subsystem for Linux.

    WSL sets WSL_DISTRO_NAME (and WSL_INTEROP) in every shell; the
    kernel release string names Microsoft as a fallback for a scrubbed
    environment. A missing or unreadable osrelease means not Linux, so
    not WSL — an answer, not a failure.
    """
    environ = os.environ if environ is None else environ
    if environ.get("WSL_DISTRO_NAME") or environ.get("WSL_INTEROP"):
        return True
    try:
        return "microsoft" in osrelease.read_text(encoding="utf-8").lower()
    except (OSError, UnicodeDecodeError):
        return False


def detect_clipboard_command(*, platform: Optional[str] = None,
                             environ: Optional[dict] = None,
                             which: Optional[Callable] = None,
                             wsl: Optional[bool] = None) -> Optional[str]:
    """The CLIPBOARD_ALTERNATIVES value this machine looks set up for.

    The environment picks the candidates — macOS: pbcopy; Windows or
    WSL: clip.exe; otherwise WAYLAND_DISPLAY: wl-copy, then DISPLAY:
    xclip, then xsel — and the first whose program is on PATH wins. No
    signal, or no program found, is None: the screen then lists the
    alternatives with nothing marked. Never runs the command.
    """
    platform = sys.platform if platform is None else platform
    environ = os.environ if environ is None else environ
    which = shutil.which if which is None else which
    if platform == "darwin":
        candidates = ["pbcopy"]
    elif platform in ("win32", "cygwin", "msys"):
        candidates = ["clip.exe"]
    elif (is_wsl(environ) if wsl is None else wsl):
        candidates = ["clip.exe"]
    else:
        candidates = []
        if environ.get("WAYLAND_DISPLAY"):
            candidates.append("wl-copy")
        if environ.get("DISPLAY"):
            candidates += ["xclip -selection clipboard",
                           "xsel --clipboard --input"]
    for command in candidates:
        if which(command.split()[0]):
            return command
    return None


def clipboard_alternatives(**detect) -> list:
    """Every CLIPBOARD_ALTERNATIVES value, the detected one marked
    (keyword arguments pass through to detect_clipboard_command)."""
    found = detect_clipboard_command(**detect)
    return bale_wizard.detected_first(
        bale_wizard.Alternative(value, note, value == found)
        for value, note in CLIPBOARD_ALTERNATIVES)


def search_path_alternatives(*, home: Optional[Path] = None,
                             environ: Optional[dict] = None,
                             wsl: Optional[bool] = None,
                             windows_users: Path = Path("/mnt/c/Users"),
                             ) -> list:
    """The inbound directories that exist on this machine.

    Under WSL, each person's Windows-side Downloads
    (/mnt/c/Users/<you>/Downloads), the profile matching $USER first, at
    most WINDOWS_DOWNLOADS_MAX; and the home directory's Downloads,
    offered as `~/Downloads` because search_paths expands tilde at use
    time — the literal stays portable in a committed file. Only
    directories that exist are offered, each marked detected; none is
    an empty list (the screen as it was).
    """
    environ = os.environ if environ is None else environ
    home = Path.home() if home is None else home
    found: list = []
    if is_wsl(environ) if wsl is None else wsl:
        try:
            profiles = sorted(windows_users.iterdir())
        except OSError:
            profiles = []  # no Windows drive mounted: nothing to offer
        me = (environ.get("USER") or "").lower()
        downloads = [p / "Downloads" for p in profiles
                     if p.name.lower() not in _WINDOWS_NON_PROFILES
                     and (p / "Downloads").is_dir()]
        downloads.sort(key=lambda d: (d.parent.name.lower() != me,
                                      d.parent.name.lower()))
        found += [bale_wizard.Alternative(str(d), "Windows Downloads", True)
                  for d in downloads[:WINDOWS_DOWNLOADS_MAX]]
    if (home / "Downloads").is_dir():
        found.append(bale_wizard.Alternative("~/Downloads", "home Downloads",
                                             True))
    return found


def _run_git(args: list, cwd: Optional[Path]):
    """One detection git call: (completed process, None) or (None, why).

    Never raises: a missing git, a timeout, or an OS error comes back as
    a short reason for the key's dim note.
    """
    try:
        return subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True,
            stdin=subprocess.DEVNULL, timeout=DETECTION_TIMEOUT), None
    except FileNotFoundError:
        return None, "git not found"
    except subprocess.TimeoutExpired:
        return None, f"git timed out after {DETECTION_TIMEOUT}s"
    except OSError as e:
        return None, f"git could not run ({e})"


def detect_git_user_name(repo: Optional[Path]) -> tuple[Optional[str],
                                                         Optional[str]]:
    """git's user.name as (name, None), (None, None) when unset, or
    (None, reason) when git could not answer.

    With a repo, every scope git consults there (repo-local over
    global); without one (the global wizard), the global scope alone, so
    the answer does not depend on whatever directory the wizard ran in.
    """
    args = (["config", "--get", "user.name"] if repo is not None
            else ["config", "--global", "--get", "user.name"])
    result, why = _run_git(args, repo)
    if result is None:
        return None, why
    if result.returncode == 0:
        return (result.stdout.strip() or None), None
    if result.returncode == 1:
        return None, None  # git's "key not set" exit: nothing found
    return None, f"git config exited {result.returncode}"


def untracked_input_alternatives(repo: Path) -> tuple[list, Optional[str]]:
    """UNTRACKED_INPUT_CANDIDATES present at the repo root and untracked.

    "Untracked" means git tracks nothing at or under the path (a
    gitignored directory is the usual case). Returns (alternatives,
    reason) — reason set only when git could not answer, in which case
    nothing is offered rather than a guess.
    """
    present = [name for name in UNTRACKED_INPUT_CANDIDATES
               if (repo / name).exists()]
    if not present:
        return [], None
    result, why = _run_git(["ls-files", "-z", "--", *present], repo)
    if result is None:
        return [], why
    if result.returncode != 0:
        return [], f"git ls-files exited {result.returncode}"
    tracked = {path.split("/", 1)[0]
               for path in result.stdout.split("\0") if path}
    return [bale_wizard.Alternative(name, "present, untracked", True)
            for name in present if name not in tracked], None


def archive_dir_alternatives(agent_dir: str,
                             repo: Optional[Path]) -> list:
    """`<agent_dir>/responses`, the response-archive convention;
    detected when the directory already exists in the repo."""
    value = f"{agent_dir}/responses"
    exists = repo is not None and (repo / value).is_dir()
    return [bale_wizard.Alternative(
        value, "exists" if exists else "the archive convention", exists)]


def validation_base_alternatives(agent_dir: str,
                                 repo: Optional[Path]) -> list:
    """Both checkpoint conventions, always: the per-session
    `<agent_dir>/checkpoints/{sid}.sh` and the shared
    `scripts/validation.base.sh`. Each is detected when its directory
    (per-session) or file (shared) is already in the repo."""
    per_session = f"{agent_dir}/checkpoints/{{sid}}.sh"
    shared = "scripts/validation.base.sh"
    has_dir = repo is not None and (repo / agent_dir / "checkpoints").is_dir()
    has_file = repo is not None and (repo / shared).is_file()
    return bale_wizard.detected_first([
        bale_wizard.Alternative(per_session, "one per session", has_dir),
        bale_wizard.Alternative(shared, "one shared script", has_file),
    ])


def staging_strategy_alternatives() -> list:
    """Both STAGING_STRATEGIES, named; nothing to detect."""
    return [
        bale_wizard.Alternative("working-tree", "default: the checkout"),
        bale_wizard.Alternative("target-base", "the target tip's tree"),
    ]


def _baked_in_exclude_dirs() -> frozenset:
    """Pack's baked-in excluded directory names, for the .baleignore
    signals (a file pack never ships needs no pattern).

    Read from bale_pack, the constant's one home, lazily (the module is
    large and only this step needs it). If it cannot be read — the name
    moved — the suggestions simply count those files too: noisier, never
    wrong about what a pattern would match, and the wizard still runs.
    """
    try:
        import bale_pack  # lazy: see the docstring
        return frozenset(bale_pack.BAKED_IN_EXCLUDE_DIRS)
    except (ImportError, AttributeError):
        return frozenset()


def _human_size(size: int) -> str:
    """1024-based, one decimal under 10 (pack's size idiom)."""
    if size < 1024:
        return f"{size} B"
    units = ("KB", "MB", "GB")
    value, index = size / 1024, 0
    while value >= 1024 and index < len(units) - 1:
        value, index = value / 1024, index + 1
    return (f"{value:.1f} {units[index]}" if value < 10
            else f"{value:.0f} {units[index]}")


def baleignore_suggestions(repo: Path,
                           existing: Sequence[str] = ()
                           ) -> tuple[list, Optional[str]]:
    """.baleignore patterns drawn from what this repo would ship.

    Lists what pack lists (git ls-files --cached --others
    --exclude-standard), drops what pack's baked-in exclusions already
    drop, and groups the rest under three signals, in this order of
    precedence for any one file: a directory in BALEIGNORE_SUGGEST_DIRS
    on its path (suggested as `name/`), an extension in
    BALEIGNORE_SUGGEST_EXTENSIONS (`*.ext`, in the case found), or a
    single file of at least BALEIGNORE_LARGE_FILE_BYTES (its own path,
    `/name` at the root so the pattern stays anchored). Patterns already
    in `existing` are not offered again. The heaviest
    BALEIGNORE_SUGGESTIONS_MAX are returned, each aside giving the file
    count and total size; (alternatives, reason) — reason set only when
    git could not list the files.
    """
    result, why = _run_git(
        ["ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        repo)
    if result is None:
        return [], why
    if result.returncode != 0:
        return [], f"git ls-files exited {result.returncode}"
    baked = _baked_in_exclude_dirs()
    have = {p.strip() for p in existing}
    groups: dict = {}
    for rel in (p for p in result.stdout.split("\0") if p):
        parts = rel.split("/")
        if any(part in baked for part in parts):
            continue
        try:
            size = (repo / rel).stat().st_size
        except OSError:
            continue  # listed but gone (deleted, not yet staged): not shipped
        folder = next((part for part in parts[:-1]
                       if part in BALEIGNORE_SUGGEST_DIRS), None)
        suffix = Path(parts[-1]).suffix
        if folder is not None:
            pattern = f"{folder}/"
        elif suffix[1:].lower() in BALEIGNORE_SUGGEST_EXTENSIONS:
            pattern = f"*{suffix}"
        elif (size >= BALEIGNORE_LARGE_FILE_BYTES
              and not any(ch in rel for ch in "*?[]")):
            pattern = rel if "/" in rel else f"/{rel}"
        else:
            continue
        count, total = groups.get(pattern, (0, 0))
        groups[pattern] = (count + 1, total + size)
    ranked = sorted(((p, c, t) for p, (c, t) in groups.items()
                     if p not in have),
                    key=lambda row: (-row[2], row[0]))
    return [bale_wizard.Alternative(
                pattern,
                f"{count} file{'' if count == 1 else 's'}, "
                f"{_human_size(total)}")
            for pattern, count, total in
            ranked[:BALEIGNORE_SUGGESTIONS_MAX]], None


def _agent_dir_for_suggestions(existing: dict, layer: str) -> str:
    """The agent directory the conventions are spelled under: the
    project file's [layout] agent_dir when usable, else the default (the
    global layer has no [layout])."""
    if layer == "project":
        layout = existing.get("layout")
        raw = layout.get("agent_dir") if isinstance(layout, dict) else None
        if isinstance(raw, str) and raw.strip() \
                and layout_agent_dir_problem(raw.strip()) is None:
            return raw.strip()
    return DEFAULT_AGENT_DIR


def suggest_wizard_values(layer: str, existing: Optional[dict] = None, *,
                          repo: Optional[Path] = None,
                          config_path: Optional[Path] = None,
                          environ: Optional[dict] = None,
                          home: Optional[Path] = None,
                          platform: Optional[str] = None,
                          which: Optional[Callable] = None,
                          wsl: Optional[bool] = None) -> WizardSuggestions:
    """Gather every key's alternatives for one walk at `layer`.

    Machine-level offers (the clipboard command, the inbound
    directories, git's user.name) are made at both layers; repo-level
    ones (untracked inputs, which conventions already exist) only when
    `repo` is given. `config_path`, the file being walked, lets the
    clipboard screen warn when that file spells the key in a form the
    probe scaffold's reader cannot see. The keyword arguments after it
    stand in for the machine in tests.
    """
    existing = existing or {}
    out = WizardSuggestions()
    agent_dir = _agent_dir_for_suggestions(existing, layer)

    out.alternatives["apply.search_paths"] = search_path_alternatives(
        home=home, environ=environ, wsl=wsl)
    out.alternatives["apply.archive_dir"] = archive_dir_alternatives(
        agent_dir, repo)
    out.alternatives["staging.strategy"] = staging_strategy_alternatives()
    if repo is not None:
        inputs, why = untracked_input_alternatives(repo)
        out.alternatives["staging.untracked_inputs"] = inputs
        if why:
            out.note("staging.untracked_inputs", f"detection skipped: {why}")
    name, why = detect_git_user_name(repo)
    if name:
        out.alternatives["identity.packer"] = [
            bale_wizard.Alternative(name, "git user.name", True)]
    elif why:
        out.note("identity.packer", f"detection skipped: {why}")
    out.alternatives["probe.clipboard_command"] = clipboard_alternatives(
        platform=platform, environ=environ, which=which, wsl=wsl)
    if layer == "project":
        out.alternatives["validation.base"] = validation_base_alternatives(
            agent_dir, repo)

    probe = existing.get("probe")
    raw = probe.get("clipboard_command") if isinstance(probe, dict) else None
    if config_path is not None and isinstance(raw, str) and raw.strip():
        problem = clipboard_command_spelling_problem(config_path)
        if problem is not None:
            out.warn("probe.clipboard_command",
                     f"this file's clipboard_command {problem}, which the "
                     f"probe scaffold's reader cannot see; writing the "
                     f"file rewrites it as a one-line string.")
    return out


def _help_paragraphs(description: list[str]) -> list[str]:
    """A key's full description as one re-flowable paragraph.

    The descriptions are written as pre-broken lines for the old fixed
    indent; the layer re-wraps them to the width, so they are joined
    first. A line ending in a hyphen before a lowercase word was a word
    broken across lines ("response-" / "script"), joined without a space.
    """
    text = ""
    for line in (ln.strip() for ln in description):
        if not line:
            continue
        if text.endswith("-") and line[:1].islower():
            text += line
        else:
            text = f"{text} {line}" if text else line
    return [text] if text else []


def _enter_action(*, unset: bool, suppressed: bool, inherits: bool) -> str:
    """What Enter does at this item, in the prompt's words."""
    if unset:
        return "Enter keeps inheriting" if inherits else "Enter leaves it unset"
    if suppressed:
        return "Enter keeps it suppressed"
    return "Enter keeps current"


def _show_help(walk: bale_wizard.Walk, label: str, description: list[str],
               answers: str):
    """The '?' callback for one item."""
    return lambda: walk.ui.help(label, _help_paragraphs(description), answers)


def wizard_grammar(ui: bale_wizard.WizardUI, *, layer: str) -> None:
    """The answer grammar, explained once, before the first key.

    Per-item prompts only state what Enter does and offer '?'; this table
    is the one place the rest of the grammar is spelled out (and each
    item's '?' help repeats the line that applies to it).
    """
    ui.heading("How to answer")
    ui.emit("Each key gets one screen: a short summary, its state, and a "
            "prompt that says what Enter does there. Every key is "
            "optional.", indent=2)
    rows = [
        ("Enter", "keep: each prompt says what that means for its key"),
        ("a value", "set the key at this layer: true or false for on/off "
                    "keys, colon-separated entries for lists"),
        ("a number", "set the numbered alternative listed above the "
                     "prompt, the same as typing it (in a list, numbers "
                     "and values mix: 1:2)"),
        ("-", "clear the key at this layer"
              + ("; a global value then applies" if layer == "project"
                 else "")),
    ]
    if layer == "project":
        rows.append(("x", "suppress an inherited global value (offered on "
                          "keys that show one)"))
    rows.append(("?", "show the key's full description, then answer"))
    ui.table(rows, indent=4)
    ui.emit("Nothing is written until the review after the last key.",
            indent=2)


def _screen_extras(walk: bale_wizard.Walk,
                   suggestions: Optional[WizardSuggestions],
                   label: str) -> list:
    """Draw a key's notes and warnings, then its numbered alternatives;
    return the alternatives in screen order (empty when none)."""
    if suggestions is None:
        return []
    for text in suggestions.warnings.get(label, ()):
        walk.ui.warn(text)
    for text in suggestions.notes.get(label, ()):
        walk.ui.emit(text, indent=bale_wizard.BODY_INDENT, style=("dim",))
    alternatives = suggestions.for_key(label)
    walk.ui.alternatives(alternatives)
    return alternatives


_PICK_ANSWER = (" · a number sets the alternative listed above, the same "
                "as typing it")


def _ask_with_alternatives(walk: bale_wizard.Walk, alternatives: list,
                           enter_action: str, show_help,
                           separator: Optional[str] = None
                           ) -> Optional[str]:
    """ask_item on a screen without alternatives (unchanged), ask_choice
    on one with them."""
    if not alternatives:
        return walk.ui.ask_item(enter_action, show_help=show_help)
    return walk.ui.ask_choice(enter_action, count=len(alternatives),
                              show_help=show_help, separator=separator)


def _picked(entry: str, alternatives: list) -> str:
    """`entry` with an in-range number replaced by its alternative's
    value (ask_choice has already re-asked on any out-of-range one)."""
    number = bale_wizard.pick_number(entry)
    if number is not None and 1 <= number <= len(alternatives):
        return alternatives[number - 1].value
    return entry


def _prompt_value(walk: bale_wizard.Walk, label: str, *,
                  current: Optional[str],
                  inherited: Optional[str] = None,
                  kind: str = "text",
                  summary,
                  description: list[str],
                  unset_effective: str = "(no hook will run)",
                  suggestions: Optional[WizardSuggestions] = None,
                  ) -> Optional[str]:
    """Generic value-prompt for the wizard.

    `walk` draws the screen (bale_wizard); `label` is the dotted key.
    `summary` is the short default view; `description` is the full text
    shown on '?'. `kind` names the answer shape on the item header.

    `suggestions` (session wizard-defaults) carries the key's numbered
    alternatives and any note or warning for its screen; with
    alternatives, a typed number in range sets that alternative's value
    — exactly as if the value had been typed, so every check the caller
    runs after the prompt applies to it too — and one out of range is
    re-asked (bale_wizard.ask_choice). Every other answer below keeps
    its meaning.

    `unset_effective` is the effective-line rendering when no layer sets
    the key (or this layer suppresses it). The default keeps the hook
    keys' wording; every non-hook string key passes its own, so the
    wizard never tells the operator an unset archive_dir or packer means
    "no hook will run" (the _prompt_bool precedent).

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
      - '?'                 → show the full description, ask again (consumed
                              by the presentation layer; never a value).
      - any other text      → return that text (set value).
      - EOF/^C              → keep current (safer than clearing).

    Display shows current AND inherited AND the effective value the merge
    would produce, so the user sees at a glance what they're about to keep,
    change, or override.
    """
    ui = walk.ui
    walk.begin(label, kind=kind, summary=summary)

    if current is None:
        current_shown = "(unset)"
    elif current == "":
        current_shown = '(suppressed: "" ignores the inherited value)'
    else:
        current_shown = current
    rows: list = [("current", current_shown)]
    aside = [""]
    # Inherited shows only when this is the project layer and the global
    # layer has a value; the 'x' sigil is offered exactly then.
    if inherited:
        rows.append(("inherited", inherited))
        aside.append("from global; x suppresses")

    # Effective value the merge would produce given current state.
    if current is None:
        effective = inherited
    elif current == "":
        effective = None
    else:
        effective = current
    rows.append(("effective", effective if effective else unset_effective))
    aside.append("")
    ui.state(rows, aside)
    alternatives = _screen_extras(walk, suggestions, label)

    answers = ("Answers: Enter keeps · a value sets it at this layer "
               "· - clears it at this layer")
    if inherited:
        answers += (" · x suppresses the inherited value (writes an "
                    "empty string)")
    if alternatives:
        answers += _PICK_ANSWER
    raw = _ask_with_alternatives(
        walk, alternatives,
        _enter_action(unset=current is None, suppressed=current == "",
                      inherits=bool(inherited)),
        _show_help(walk, label, description, answers))
    if raw is None:
        return current
    val = _picked(raw, alternatives)
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
        ui.warn(f"'{val}' is the suppression sigil, only meaningful when a "
                f"global value is inherited. No global value is set for "
                f"this key; keeping current.")
        return current
    return val


def _prompt_bool(walk: bale_wizard.Walk, label: str, *,
                 current: Optional[bool],
                 inherited: Optional[bool] = None,
                 summary,
                 description: list[str],
                 unset_effective: str = "(unset — off)") -> Optional[bool]:
    """Boolean prompt for the wizard, mirroring `_prompt_value` semantics.

    `unset_effective` is the effective-line rendering when no layer
    sets the key. The default reads "off" because every bool the
    wizard walked until v0.4.26 defaulted false; a default-true key
    (sandbox.enabled) passes its own wording so the wizard never tells
    the operator an absent key means the sandbox is off.

    States at this layer:
      - None  — key absent. Inherit if a lower layer sets it; unset otherwise.
      - True / False — key set.

    No 'x' suppress sigil: booleans have no empty form, and an explicit
    `false` at the project layer already overrides an inherited `true`
    (per-key replacement). The inherited row and the '?' help say so.

    Input semantics:
      - Enter               → keep current (None/True/False as passed in).
      - true/t/yes/y/1      → True.
      - false/f/no/n/0      → False.
      - '-'                 → None (clear at this layer).
      - '?'                 → show the full description, ask again.
      - anything else       → keep current, with a hint.
      - EOF/^C              → keep current (safer than clearing).
    """
    def _show(v: Optional[bool]) -> str:
        return "(unset)" if v is None else ("true" if v else "false")

    ui = walk.ui
    walk.begin(label, kind="true/false", summary=summary)

    rows: list = [("current", _show(current))]
    aside = [""]
    if inherited is not None:
        rows.append(("inherited", _show(inherited)))
        aside.append("from global; false here overrides")
    effective = current if current is not None else inherited
    rows.append(("effective",
                 unset_effective if effective is None else _show(effective)))
    aside.append("")
    ui.state(rows, aside)

    answers = ("Answers: Enter keeps · true or false (also y/n, yes/no, "
               "1/0) sets it at this layer · - clears it at this layer")
    if inherited is not None:
        answers += (" · no 'x' sigil for booleans: an explicit 'false' "
                    "here already overrides the inherited value")
    raw = ui.ask_item(
        _enter_action(unset=current is None, suppressed=False,
                      inherits=inherited is not None),
        show_help=_show_help(walk, label, description, answers))
    if raw is None:
        return current
    val = raw.lower()
    if val == "":
        return current
    if val == "-":
        return None
    if val in ("true", "t", "yes", "y", "1"):
        return True
    if val in ("false", "f", "no", "n", "0"):
        return False
    ui.warn(f"'{bale_wizard.clip(raw)}' is not a boolean; expected "
            f"true/false (or Enter to keep, '-' to clear). Keeping current.")
    return current


def _prompt_path_list(walk: bale_wizard.Walk, label: str, *,
                      current: Optional[list[str]],
                      inherited: Optional[list[str]] = None,
                      kind: str = "paths, colon-separated",
                      summary,
                      description: list[str],
                      unset_effective: str = "(no extra search paths)",
                      suggestions: Optional[WizardSuggestions] = None,
                      ) -> Optional[list[str]]:
    """List-of-paths prompt for the wizard, mirroring `_prompt_value` semantics.

    `suggestions` works as in `_prompt_value`, entry by entry: each
    colon-separated entry that is an in-range number becomes that
    alternative's value, so `1` sets a one-entry list, `1:2` takes two
    alternatives, and `1:inbox` mixes a pick with a typed path.

    `unset_effective` is the effective-line rendering when the list is
    unset or suppressed. The default keeps apply.search_paths' wording;
    the other list keys (check names, untracked inputs, group paths)
    pass their own.

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
      - '?'                                  → show the full description,
                                               ask again.
      - colon-separated paths                → return parsed list (empties
                                               dropped — stray colons in input
                                               shouldn't introduce ""-entries).
      - EOF/^C                               → keep current.

    The display prefers one path per line — colon-joined lists are
    unreadable at length. This is the canonical wizard interface for list-
    shaped configurables; future list-shaped configurables should reuse this.
    """
    ui = walk.ui
    walk.begin(label, kind=kind, summary=summary)

    if current is None:
        current_shown: object = "(unset)"
    elif current == []:
        current_shown = "(suppressed: empty list)"
    else:
        current_shown = list(current)
    rows: list = [("current", current_shown)]
    aside = [""]
    if inherited:
        rows.append(("inherited", list(inherited)))
        aside.append("from global; x suppresses")

    if current is None:
        effective = inherited
    elif current == []:
        effective = None
    else:
        effective = current
    rows.append(("effective", list(effective) if effective
                 else unset_effective))
    aside.append("")
    ui.state(rows, aside)
    alternatives = _screen_extras(walk, suggestions, label)

    answers = ("Answers: Enter keeps · colon-separated entries set the "
               "list at this layer · - clears it at this layer")
    if inherited:
        answers += (" · x suppresses the inherited list (writes an "
                    "empty list)")
    if alternatives:
        answers += (" · a number sets the alternative listed above as an "
                    "entry, the same as typing it (1:2 takes two)")
    raw = _ask_with_alternatives(
        walk, alternatives,
        _enter_action(unset=current is None, suppressed=current == [],
                      inherits=bool(inherited)),
        _show_help(walk, label, description, answers), separator=":")
    if raw is None:
        return current
    val = raw
    if val == "":
        return current
    if val == "-":
        return None
    if val == "x":
        if inherited:
            return []
        ui.warn(f"'{val}' is the suppression sigil, only meaningful when a "
                f"global value is inherited. No global value is set for "
                f"this key; keeping current.")
        return current
    # Drop empties — stray colons in input shouldn't introduce ""-entries
    # that then survive into bale.toml. Numbers become their alternatives
    # entry by entry (a no-op on a screen without alternatives).
    parts = [_picked(p.strip(), alternatives) for p in val.split(":")]
    parts = [p for p in parts if p]
    return parts or None


def walkthrough_git_identity(
        repo: Path, ui: Optional[bale_wizard.WizardUI] = None) -> None:
    """Per constraint: check git user.name and user.email; if either is
    unset, prompt and write to the repo-local git config (never --global).

    Idempotent: already-set values (from any scope, repo-local or global)
    are reported and left alone. The constraint says "if unset, prompt
    and write to local" — already-set anywhere counts as set.

    Shared with bale_pack's git-init walkthrough, which calls it with the
    repo alone; `ui` defaults to a fresh WizardUI either way.
    """
    from __main__ import git

    ui = ui or bale_wizard.WizardUI()
    ui.heading("Git identity", "commit attribution on bale apply")
    width = len("git user.email")
    for key, label in (("user.name", "name"), ("user.email", "email")):
        result = git(["config", "--get", key], cwd=repo, check=False)
        current = result.stdout.strip() if result.returncode == 0 else ""
        row_label = f"git {key}".ljust(width)
        if current:
            ui.table([(row_label, current)], indent=2, aside=["set"])
            continue
        ui.table([(row_label, "(unset)")], indent=2)
        val = ui.ask(f"enter your {label} · Enter skips > ", indent=2)
        val = val or ""
        if val:
            # Repo-local. Never --global per the constraint.
            git(["config", key, val], cwd=repo)
            ui.notice(f"wrote {key} = {val} to repo-local git config",
                      indent=2)
        else:
            ui.notice(f"skipped; commits during this session may be "
                      f"attributed to a fallback identity until {key} is "
                      f"set.", indent=2)


def walk_configurables(existing: dict, *, layer: str,
                       inherited: Optional[dict] = None,
                       ui: Optional[bale_wizard.WizardUI] = None,
                       repo: Optional[Path] = None,
                       suggestions: Optional[WizardSuggestions] = None,
                       ) -> dict:
    """Walk every configurable; return the new dict for the layer being edited.

    `existing` is the current contents of the file being written. `layer` is
    "project" or "global". `inherited` is the lower layer (the global config)
    when walking the project layer, or None when walking global (no layer
    below to inherit from). `ui` is the presentation layer to draw with
    (default: a fresh bale_wizard.WizardUI).

    `suggestions` (session wizard-defaults) is what the walk offers beside
    its prompts: the numbered alternatives, detected values first, and any
    note or warning per key. None gathers them now from this machine and,
    when `repo` is given, from the repo (suggest_wizard_values); an empty
    WizardSuggestions() offers nothing, drawing every screen as it was
    before alternatives existed. Offers never change what Enter means.

    The presence of a key in the returned dict, including the empty-string /
    empty-list "suppress" form, determines what render_bale_toml emits.

    Sessions adding new configurables extend this function in the same
    response — and WIZARD_WALK_ORDER_* above, which the walk refuses to
    run without. The wizard is the discoverable surface; if a configurable
    isn't here, there's no canonical way to opt in to it.
    """
    if layer not in ("project", "global"):
        raise ValueError(f"unknown layer: {layer!r}")
    inherited = inherited or {}
    walk = _wizard_walk(layer, ui)
    if suggestions is None:
        suggestions = suggest_wizard_values(layer, existing, repo=repo)

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
        walk, "hooks.post_pack",
        kind="script path",
        summary=(
            "Script bale runs after `bale pack` writes a request tarball "
            "(bale asks before running it)."
        ),
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
        walk, "hooks.post_apply_pass",
        kind="script path",
        summary=(
            "Script bale runs after a passing `bale apply` merges (bale "
            "asks before running it)."
        ),
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
        walk, "apply.search_paths",
        suggestions=suggestions,
        kind="paths, colon-separated",
        summary=(
            "Directories searched, after cwd, for a relative inbound-file"
            " name: tarballs, briefs, bundles, checkpoint files."
        ),
        current=current_list,
        inherited=inh_list,
        description=[
            "Optional. Enter to skip; you can wire one up later.",
            "Directories bale searches when a command is given a relative",
            "inbound-file name: the tarball for `bale apply` / `bale",
            "retry` / `bale handoff`, the bundle for `bale open`, the",
            "file for `bale relay` and `bale amend-checkpoint`, and the",
            "prose or checkpoint file for `bale pack --readme-file` /",
            "`--checkpoint-file`. Tried in order; first match wins. An",
            "absolute path argument bypasses search. Cwd is always tried",
            "first implicitly — you don't need to list it. Bare `bale",
            "apply` (no tarball named) looks for the newest",
            "response-*.tar.gz across cwd and these directories.",
            "Tilde (~/Downloads) and env vars ($HOME/Downloads) expand at",
            "use time, so the committed file stays portable across machines.",
            "Use case: worker files land in ~/Downloads; with ~/Downloads",
            "here, a bare `bale apply` and `bale pack ... --readme-file",
            "brief.md` both work from anywhere in the repo.",
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
        walk, "apply.no_interact",
        summary=(
            "true = `bale apply` and `bale retry` run non-interactively, "
            "each prompt taking its default (logged)."
        ),
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
        walk, "apply.hook_auto_accept",
        summary=(
            "Non-interactive mode only: true = hooks run without their "
            "confirmation prompt."
        ),
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

    # ---- [apply].archive_dir -------------------------------------------------
    # String value with the standard ""-suppress form when a global value
    # is inherited; walked at both layers like the sibling [apply] keys.
    # The strict shape checks (repo-relative, no '..') live in the typed
    # accessor at read time — the wizard reads raw and tolerates oddness,
    # same defensive posture as the list/bool keys above.
    raw_cur = existing_apply.get("archive_dir")
    current = raw_cur if isinstance(raw_cur, str) else None
    raw_inh = inherited_apply.get("archive_dir")
    inh = raw_inh.strip() if isinstance(raw_inh, str) and raw_inh.strip() else None

    val = _prompt_value(
        walk, "apply.archive_dir",
        suggestions=suggestions,
        kind="repo-relative dir",
        summary=(
            "Directory a merged response's README.md and notes.md are "
            "copied into, untracked."
        ),
        current=current,
        inherited=inh,
        description=[
            "Optional. Enter to skip; you can wire one up later.",
            "Repo-relative directory of this project's response-archive",
            "convention (e.g. claude/responses). When set, a successful",
            "`bale apply` merge copies whichever of the response's",
            "README.md and notes.md the response included into",
            "<archive_dir>/<sid>/ as untracked working-tree files, so",
            "worker prose is include-ready for later packs without the",
            "extract-rename round. Committing the copies stays your job",
            "— bale never auto-commits. Unset = no archival. HOLDs,",
            "reverts, bailouts, and clarifications archive nothing.",
        ],
        unset_effective="(unset — no archival)",
    )
    if val is not None:
        new.setdefault("apply", {})["archive_dir"] = val

    # ---- [apply].sweep -------------------------------------------------------
    # Bool with the standard prompt shape; walked at both layers like
    # the sibling [apply] bools (an explicit project-layer false
    # overrides an inherited global true via per-key replacement).
    raw_cur_b = existing_apply.get("sweep")
    current_b = raw_cur_b if isinstance(raw_cur_b, bool) else None
    raw_inh_b = inherited_apply.get("sweep")
    inh_b = raw_inh_b if isinstance(raw_inh_b, bool) else None

    val_b = _prompt_bool(
        walk, "apply.sweep",
        summary=(
            "true = at a session-closing event, bale commits exactly the "
            "bookkeeping files it just wrote."
        ),
        current=current_b,
        inherited=inh_b,
        description=[
            "Optional. Enter to skip.",
            "true = after bale finishes writing files it owns at a",
            "session-closing event (the telemetry record, and archive",
            "copies when apply.archive_dir is set), it stages exactly",
            "those files and commits them as `[bale sweep <sid>]",
            "<event>` — never a directory glob, never `git add -A`;",
            "your unrelated dirty files are untouched. Degenerate git",
            "states (in-progress merge, detached HEAD, no committable",
            "identity) skip loudly and leave the files for a manual",
            "sweep. false/unset = bale writes the files untracked and",
            "never commits — today's behavior (false also overrides an",
            "inherited true).",
        ],
    )
    if val_b is not None:
        new.setdefault("apply", {})["sweep"] = val_b

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
        walk, "staging.strategy",
        suggestions=suggestions,
        kind="working-tree | target-base",
        summary=(
            "How `bale apply` builds the staging tree that validation.sh "
            "runs in."
        ),
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
        unset_effective="(unset — working-tree)",
    )
    if val not in (None, "") and val.strip() not in STAGING_STRATEGIES:
        walk.ui.warn(f"'{bale_wizard.clip(val)}' is not a staging "
                     f"strategy; expected one of: "
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
        walk, "staging.untracked_inputs",
        suggestions=suggestions,
        kind="paths, colon-separated",
        summary=(
            "target-base only: untracked build or dependency paths (e.g. "
            ".venv) copied into staging."
        ),
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
        unset_effective="(none)",
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
        walk, "identity.packer",
        suggestions=suggestions,
        kind="name",
        summary=(
            "Who authors packs here; stamped into each request as "
            "provenance.packer."
        ),
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
        unset_effective="(unset — requests stamp 'unconfigured')",
    )
    if val is not None:
        new.setdefault("identity", {})["packer"] = val

    # ---- [probe].clipboard_command (both layers) ----------------------------
    # This machine's clipboard command (board 99a's key; both layers since
    # session wizard-defaults — PROBE_VALUES owns the ruling). Walked at
    # both layers with the [identity] mechanics: string value, "" suppress
    # form when a global value is inherited. The alternatives are always
    # the five named commands (CLIPBOARD_ALTERNATIVES), the detected one
    # first. The crafter-readable shape check runs after the prompt with
    # the staging.strategy reject-with-hint posture — on a picked number
    # as on a typed value — so an unreadable value keeps current rather
    # than landing a key the crafter would silently treat as unset.
    existing_probe = (existing.get("probe")
                      if isinstance(existing.get("probe"), dict) else {})
    inherited_probe = (inherited.get("probe")
                       if isinstance(inherited.get("probe"), dict) else {})
    raw_cur = existing_probe.get("clipboard_command")
    current = raw_cur if isinstance(raw_cur, str) else None
    raw_inh = inherited_probe.get("clipboard_command")
    inh = raw_inh.strip() if isinstance(raw_inh, str) and raw_inh.strip() else None

    val = _prompt_value(
        walk, "probe.clipboard_command",
        kind="shell command",
        suggestions=suggestions,
        summary=(
            "Command that copies its stdin to this machine's clipboard "
            "(pbcopy, clip.exe, ...)."
        ),
        current=current,
        inherited=inh,
        description=[
            "Optional. Enter to skip (no clipboard copy).",
            "Shell command that copies its standard input to this",
            "machine's clipboard: pbcopy (macOS), clip.exe (Windows and",
            "WSL), wl-copy (Wayland), xclip -selection clipboard or xsel",
            "--clipboard --input (X11). They are listed by number, the",
            "one detected on this machine first; detection only",
            "suggests, and nothing is set until you pick or type one.",
            "Per-machine: set it once with `bale config init --global`;",
            "a project may override it, or suppress it with x.",
            "bale copies every paste block it prints for you to carry",
            "into a chat with this command: pack's session opener,",
            "relay's exchange block, and apply's and retry's HOLD and",
            "APPLIED relay blocks, each with a one-line notice. A probe",
            "script emitted by `tools/craft_response.py --probe` copies",
            "its PROBE BEGIN/END block the same way, through the",
            "installed bale (`bale clipboard`), so it uses this machine's",
            "value, global or project, whether or not the request",
            "shipped a bale.toml. Setting the key is the opt-in to that",
            "copying, which overwrites your clipboard with each paste",
            "block; a missing or failing command never fails a command,",
            "it only says the copy did not happen. Unset, nothing is",
            "copied. One line, no backslashes or double quotes (wrap",
            "anything fancier in a script).",
        ],
        unset_effective="(unset — no clipboard copy)",
    )
    if val not in (None, ""):
        problem = probe_clipboard_command_problem(val)
        if problem is not None:
            walk.ui.warn(f"'{bale_wizard.clip(val)}' {problem}; the "
                         f"probe scaffold's reader would treat it as "
                         f"unset. Keeping current.")
            val = current
    if val is not None:
        new.setdefault("probe", {})["clipboard_command"] = val

    # ---- [validation].base (PROJECT LAYER ONLY) -----------------------------
    # Walked only in project mode, per the ratified disposition 1 recorded
    # on VALIDATION_VALUES: the checkpoint must be committed per-repo
    # regardless, and a global key would let the same value silently name
    # a different oracle in every repo it touches. `bale config init
    # --global` therefore never gains this prompt, and `inherited` is
    # deliberately not consulted (merged_config never carries a global
    # value into [validation] anyway).
    if layer == "project":
        existing_validation = (existing.get("validation")
                               if isinstance(existing.get("validation"), dict)
                               else {})
        raw_cur = existing_validation.get("base")
        current = raw_cur if isinstance(raw_cur, str) else None

        val = _prompt_value(
            walk, "validation.base",
            suggestions=suggestions,
            kind="repo-relative path",
            summary=(
                "The committed blind checkpoint script `bale apply` runs "
                "before validation.sh."
            ),
            current=current,
            inherited=None,
            description=[
                "Optional. Enter to skip; you can pin one later.",
                "Repo-relative path of this project's planner-authored",
                "BLIND CHECKPOINT script (BALE.md 8.5). When set, `bale",
                "apply` runs the committed version of this script from",
                "the session's base tree — never the response's staged",
                "copy — before the worker's validation.sh, and PASS",
                "requires both to exit 0. The script must be committed:",
                "config naming a path absent at the base tree refuses",
                "the apply loudly. The value may contain the literal",
                "token {sid}, resolved with the session id at pack",
                "time — per-session checkpoints instead of one shared",
                "oracle (BALE.md 8.5). Both conventions are offered by",
                "number: <agent_dir>/checkpoints/{sid}.sh, one script per",
                "session, and scripts/validation.base.sh, one shared",
                "script. Project-layer only — the global wizard does not",
                "walk this key.",
            ],
            unset_effective="(unset — no blind checkpoint)",
        )
        if val is not None:
            new.setdefault("validation", {})["base"] = val

        # ---- [validation].required (PROJECT LAYER ONLY) ----------------------
        # Board 6 session B: the required-check set apply's step-15 gate
        # reads. Same project-only posture as validation.base above and
        # the same list-walk machinery as staging.untracked_inputs —
        # _prompt_path_list is the canonical wizard interface for
        # list-shaped configurables (its docstring says so); check names
        # are colon-separated on input like paths are. `inherited` is
        # deliberately None: merged_config never carries a global value
        # into [validation].
        raw_cur_list = (existing_validation.get("required")
                        if "required" in existing_validation else None)
        current_list = (_coerce_path_list(raw_cur_list)
                        if raw_cur_list is not None else None)

        val_list = _prompt_path_list(
            walk, "validation.required",
            kind="names, colon-separated",
            summary=(
                "Check names every response that ships changes must declare "
                "in validation_will_run."
            ),
            current=current_list,
            inherited=None,
            description=[
                "Optional. Enter to skip.",
                "Check names the worker's validation_will_run MUST",
                "declare on every response that ships changes (BALE.md",
                "8.1 step 15) — exact string match against the manifest",
                "list. A declared check may still [SKIP] with a reason",
                "at runtime; the rule is about declaration, not forced",
                "work. Whole-project at v1 (no per-file-type keying).",
                "Colon-separated names, e.g. tests:lint. Project-layer",
                "only — the global wizard does not walk this key.",
            ],
            unset_effective="(no required checks)",
        )
        if val_list is not None:
            new.setdefault("validation", {})["required"] = val_list

        # ---- [sandbox].network (PROJECT LAYER ONLY) ----------------------
        # The ADR-0016 position-3 network grant (v0.4.5, board 10 S2).
        # Walked only in project mode, per the project-only ruling
        # recorded on SANDBOX_VALUES: the grant is planner-granted and
        # per-project ("never global"), so `bale config init --global`
        # never gains this prompt and `inherited` is deliberately not
        # consulted (merged_config never carries a global value into
        # [sandbox] anyway). Bool walk per the [apply] bools' machinery.
        existing_sandbox = (existing.get("sandbox")
                            if isinstance(existing.get("sandbox"), dict)
                            else {})
        raw_cur_b = existing_sandbox.get("network")
        current_b = raw_cur_b if isinstance(raw_cur_b, bool) else None

        val_b = _prompt_bool(
            walk, "sandbox.network",
            summary=(
                "true = this repo's confined response scripts (apply.sh, the "
                "checkpoint, validation.sh) get network."
            ),
            current=current_b,
            inherited=None,
            description=[
                "Optional. Enter to skip (network stays OFF — the floor).",
                "true = grant NETWORK to this repo's confined response-",
                "script executions (apply.sh, the blind checkpoint,",
                "validation.sh): bale passes network=True and the sandbox",
                "omits its --net leg. Filesystem confinement and the",
                "environment scrub are unchanged. For projects whose",
                "validation genuinely needs network (dependency-fetching",
                "builds) — ADR-0016's planner-granted hatch, decided here",
                "in committed config, never prompted at apply time, never",
                "worker-granted. Exercised grants are logged and stamped",
                "network_grant_exercised in telemetry (BALE.md 8.9).",
                "Project-layer only — the global wizard does not walk",
                "this key.",
            ],
        )
        if val_b is not None:
            new.setdefault("sandbox", {})["network"] = val_b

        # ---- [sandbox].enabled (PROJECT LAYER ONLY) ----------------------
        # Sandbox-off by config (v0.4.26, board 75). Walked only in
        # project mode, per the same project-only ruling as `network`
        # (SANDBOX_VALUES): a global `enabled = false` would silently
        # unconfine every repo the install touches, so the global wizard
        # never gains this prompt and `inherited` is never consulted.
        # Default-true key: Enter/absent keeps the sandbox ON; only a
        # typed `false` disables, and BALE.md §3.6's discoverable-surface
        # contract is why the wizard walks it at all.
        raw_cur_e = existing_sandbox.get("enabled")
        current_e = raw_cur_e if isinstance(raw_cur_e, bool) else None

        val_e = _prompt_bool(
            walk, "sandbox.enabled",
            # Two explicit lines: "NEVER silent" opens the second, so the
            # loudness guarantee is read whole, never split by a wrap.
            summary=(
                "false = response scripts run UNCONFINED, as --no-sandbox "
                "does.",
                "NEVER silent: each such run is FORCE-logged and stamped in "
                "telemetry.",
            ),
            current=current_e,
            inherited=None,
            description=[
                "Optional. Enter to skip (sandbox stays ON — the default).",
                "false = run this repo's response-script executions",
                "(apply.sh, the blind checkpoint, validation.sh, and the",
                "bale open checkpoint dry-run) UNCONFINED, exactly as",
                "--no-sandbox does per invocation — for hosts without",
                "unprivileged user namespaces, where every apply would",
                "otherwise need the flag typed by hand. NEVER silent: every",
                "run this disables FORCE-logs 'bale.toml [sandbox] enabled",
                "= false' as its source, and telemetry stamps",
                "sandbox_confined: false / sandbox_off_source: config",
                "(BALE.md 8.5, 8.9). Project-layer only — the global wizard",
                "does not walk this key, and a global value is ignored.",
            ],
            unset_effective="(unset — sandbox ON)",
        )
        if val_e is not None:
            new.setdefault("sandbox", {})["enabled"] = val_e

        # ---- [pack] include group (PROJECT LAYER ONLY) -------------------
        # The named include/forecast group (board 64). Walked only in
        # project mode, per the project-only ruling recorded on
        # PACK_VALUES: a group names one repo's paths, and a global
        # group would engage (and dangle) in every repo the install
        # touches. `inherited` is deliberately not consulted
        # (merged_config never carries a global value into [pack]).
        # Three keys walked as a unit — string name via _prompt_value,
        # two path lists via _prompt_path_list, the canonical wizard
        # interfaces for those shapes; the typed accessor
        # (get_pack_include_group) enforces the all-or-nothing rule at
        # read time.
        existing_pack = (existing.get("pack")
                         if isinstance(existing.get("pack"), dict)
                         else {})
        raw_cur = existing_pack.get("include_group")
        current = raw_cur if isinstance(raw_cur, str) else None

        val = _prompt_value(
            walk, "pack.include_group",
            kind="name",
            summary=(
                "Name of the include group: paths a pack pulls in whenever "
                "its includes touch the group's triggers."
            ),
            current=current,
            inherited=None,
            description=[
                "Optional. Enter to skip; you can pin one later.",
                "Name of this project's INCLUDE GROUP (BALE.md 7.2):",
                "when a pack's resolved includes touch any of the",
                "trigger paths (next prompt), bale pulls the group's",
                "paths (the prompt after) into the shipped context",
                "automatically, with a loud report line. Read-side",
                "only — the write forecast is never widened. The name",
                "is what report lines and the --no-include-group",
                "opt-out flag spell. Setting it requires both list",
                "keys below (a half-configured group refuses loudly).",
                "Project-layer only — the global wizard does not walk",
                "this key.",
            ],
            unset_effective="(unset — no include group)",
        )
        if val is not None:
            new.setdefault("pack", {})["include_group"] = val

        raw_cur_list = (existing_pack.get("include_group_triggers")
                        if "include_group_triggers" in existing_pack
                        else None)
        current_list = (_coerce_path_list(raw_cur_list)
                        if raw_cur_list is not None else None)

        val_list = _prompt_path_list(
            walk, "pack.include_group_triggers",
            kind="paths, colon-separated",
            summary=(
                "Paths that engage the include group (required once the group"
                " has a name)."
            ),
            current=current_list,
            inherited=None,
            description=[
                "Optional; required when pack.include_group is set.",
                "Repo-relative TRIGGER paths for the include group:",
                "the group engages when a pack's resolved include set",
                "intersects any entry (directory entries cover their",
                "subtrees). Colon-separated paths, e.g. bin:tests.",
                "Project-layer only.",
            ],
            unset_effective="(none)",
        )
        if val_list is not None:
            new.setdefault("pack", {})["include_group_triggers"] = val_list

        raw_cur_list = (existing_pack.get("include_group_pulls")
                        if "include_group_pulls" in existing_pack
                        else None)
        current_list = (_coerce_path_list(raw_cur_list)
                        if raw_cur_list is not None else None)

        val_list = _prompt_path_list(
            walk, "pack.include_group_pulls",
            kind="paths, colon-separated",
            summary=(
                "Paths the engaged group adds to the pack's shipped context "
                "(required once the group has a name)."
            ),
            current=current_list,
            inherited=None,
            description=[
                "Optional; required when pack.include_group is set.",
                "Repo-relative paths the engaged group PULLS into the",
                "pack's shipped context (files or directories). Each",
                "must exist when the group engages — a dangling entry",
                "refuses the pack loudly rather than thinning the",
                "context silently. Colon-separated paths, e.g.",
                "install.sh:docs. Project-layer only.",
            ],
            unset_effective="(none)",
        )
        if val_list is not None:
            new.setdefault("pack", {})["include_group_pulls"] = val_list

        # ---- [layout].agent_dir (PROJECT LAYER ONLY) ----------------------
        # The agent-facing directory name (v0.4.42; see LAYOUT_VALUES).
        # Walked only in project mode because the value names a
        # directory of this repo's tree; `inherited` is deliberately
        # None (and merged_config never inherits [layout]), so 'x' is
        # never offered. An escaping path is refused after the prompt
        # with the staging.strategy reject-with-hint posture: keep
        # current rather than land a key the accessor would refuse at
        # the next command.
        existing_layout = (existing.get("layout")
                           if isinstance(existing.get("layout"), dict)
                           else {})
        raw_cur = existing_layout.get("agent_dir")
        current = raw_cur if isinstance(raw_cur, str) else None

        val = _prompt_value(
            walk, "layout.agent_dir",
            kind="repo-relative dir",
            summary=(
                "Directory holding the agent-facing tree bale writes to "
                "(telemetry lives under it)."
            ),
            current=current,
            inherited=None,
            description=[
                f"Optional. Enter to skip (\"{DEFAULT_AGENT_DIR}\").",
                "Repo-relative directory holding the agent-facing tree",
                "bale writes to — the telemetry home is",
                "<agent_dir>/telemetry/ (BALE.md section 8.9). Unset =",
                f"\"{DEFAULT_AGENT_DIR}\", the directory every repo used before",
                "the key existed, so leaving it unset renames nothing.",
                "Setting it does not move an existing directory: rename",
                "the directory in git and set the key in the same commit.",
                "One repo-relative path, no '..', never absolute.",
                "Project-layer only: the value names this repo's tree,",
                "so the global wizard neither walks nor inherits it.",
            ],
            unset_effective=f"(unset — \"{DEFAULT_AGENT_DIR}\")",
        )
        if val not in (None, ""):
            problem = layout_agent_dir_problem(val.strip())
            if problem is not None:
                walk.ui.warn(f"'{bale_wizard.clip(val)}' {problem}. "
                             f"Keeping current.")
                val = current
        if val is not None:
            new.setdefault("layout", {})["agent_dir"] = val

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
# keys you hand-edited in will be dropped. There is no set/get/edit
# subcommand; the wizard is the writer.
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
        # archive_dir: string scalar (v0.5 archival), last per APPLY_VALUES
        # order. json.dumps covers it, including the empty-string suppress
        # form. Persisted literally — the repo-relative value is portable
        # by construction; validation lives in the typed accessor.
        if "archive_dir" in apply_section:
            parts.append(
                f"archive_dir = {json.dumps(apply_section['archive_dir'])}")
        # sweep: bool scalar (v0.3.32 auto-sweep), last per APPLY_VALUES
        # order. json.dumps(True) == "true", a valid TOML boolean, so
        # the same serializer covers it.
        if "sweep" in apply_section:
            parts.append(f"sweep = {json.dumps(apply_section['sweep'])}")
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

    # [validation] section (board 6 sessions A and B). Two keys: the
    # string-scalar checkpoint path (`base`, including the empty-string
    # skip form) and the list-shaped required-check set (`required`,
    # including the empty-list suppress form) — the same serialization
    # shapes the [apply]/[staging] sections cover. Emitted in
    # VALIDATION_VALUES order. Project-layer only by walk
    # (disposition 1): the global wizard never puts this section in
    # its dict, so a global bale.toml never gains it through this
    # renderer — and a hand-edited global [validation] is ignored by
    # merged_config regardless.
    validation_section = cfg.get("validation") or {}
    if validation_section:
        parts.append("[validation]")
        for key in VALIDATION_VALUES:
            if key in validation_section:
                v = validation_section[key]
                if isinstance(v, list):
                    rendered_array = ("["
                                      + ", ".join(json.dumps(p) for p in v)
                                      + "]")
                    parts.append(f"{key} = {rendered_array}")
                else:
                    parts.append(f"{key} = {json.dumps(v)}")
        parts.append("")

    # [sandbox] section (v0.4.5, board 10 S2 — the ADR-0016 network
    # grant; v0.4.26, board 75 — `enabled`). Two bool keys;
    # json.dumps(True) == "true", a valid TOML boolean, so the same
    # serializer covers both. Emitted in
    # SANDBOX_VALUES order. Project-layer only by walk (the ruling on
    # SANDBOX_VALUES): the global wizard never puts this section in
    # its dict, so a global bale.toml never gains it through this
    # renderer — and a hand-edited global [sandbox] is ignored by
    # merged_config regardless.
    sandbox_section = cfg.get("sandbox") or {}
    if sandbox_section:
        parts.append("[sandbox]")
        for key in SANDBOX_VALUES:
            if key in sandbox_section:
                parts.append(f"{key} = {json.dumps(sandbox_section[key])}")
        parts.append("")

    # [pack] section (board 64 — the named include group). One string
    # key (`include_group`, including the empty-string skip form) and
    # two path lists (the empty-list suppress form included) — the same
    # serialization shapes the sections above cover. Emitted in
    # PACK_VALUES order. Project-layer only by walk (the ruling on
    # PACK_VALUES): the global wizard never puts this section in its
    # dict, so a global bale.toml never gains it through this renderer
    # — and a hand-edited global [pack] is ignored by merged_config
    # regardless.
    pack_section = cfg.get("pack") or {}
    if pack_section:
        parts.append("[pack]")
        for key in PACK_VALUES:
            if key in pack_section:
                v = pack_section[key]
                if isinstance(v, list):
                    rendered_array = ("["
                                      + ", ".join(json.dumps(p) for p in v)
                                      + "]")
                    parts.append(f"{key} = {rendered_array}")
                else:
                    parts.append(f"{key} = {json.dumps(v)}")
        parts.append("")

    # [probe] section (board 99a — the probe scaffold's clipboard
    # epilogue). One string key, emitted in PROBE_VALUES order.
    # ensure_ascii=False is deliberate: json.dumps' default escapes
    # non-ASCII into \uXXXX sequences, and the crafter's minimal reader
    # treats any backslash as unset — so a command with a non-ASCII
    # character would round-trip through tomllib yet vanish at craft
    # time. Literal UTF-8 is a valid TOML basic string. Project-layer
    # only by walk (the ruling on PROBE_VALUES): the global wizard never
    # puts this section in its dict.
    probe_section = cfg.get("probe") or {}
    if probe_section:
        parts.append("[probe]")
        for key in PROBE_VALUES:
            if key in probe_section:
                parts.append(f"{key} = "
                             f"{json.dumps(probe_section[key], ensure_ascii=False)}")
        parts.append("")

    # [layout] section (v0.4.42 — the agent-facing directory name). One
    # string key, emitted in LAYOUT_VALUES order. Project-layer only by
    # walk (the ruling on LAYOUT_VALUES): the global wizard never puts
    # this section in its dict.
    layout_section = cfg.get("layout") or {}
    if layout_section:
        parts.append("[layout]")
        for key in LAYOUT_VALUES:
            if key in layout_section:
                parts.append(f"{key} = {json.dumps(layout_section[key])}")
        parts.append("")

    return "\n".join(parts)


def _flatten_config(cfg: dict, prefix: str = "") -> dict:
    """A parsed bale.toml as {dotted key: value}, tables recursed.

    Empty tables carry no value and are skipped; the review compares
    values, and the byte comparison beside it catches anything else.
    """
    flat: dict = {}
    for key, value in cfg.items():
        dotted = f"{prefix}{key}"
        if isinstance(value, dict):
            flat.update(_flatten_config(value, dotted + "."))
        else:
            flat[dotted] = value
    return flat


def _toml_display(value) -> str:
    """A value as it reads in bale.toml (strings quoted, lists bracketed)."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ", ".join(_toml_display(v) for v in value) + "]"
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return repr(value)


def config_changes(old: dict, new: dict, *,
                   layer: str) -> list[tuple[str, str]]:
    """What writing `new` over a file that parses to `old` changes, per key.

    Returns review rows (marker, text): "+" a key the file gains, "~" a
    key whose value changes, "-" a key the file loses. Rows follow the
    walk order, then any other keys alphabetically. A lost key the walk
    covers was cleared; one it does not cover was hand-edited in and is
    dropped by the rewrite (the header comment's warning, made visible).
    """
    before = _flatten_config(old)
    after = _flatten_config(new)
    order = wizard_walk_order(layer)
    rank = {key: i for i, key in enumerate(order)}
    keys = sorted(set(before) | set(after),
                  key=lambda k: (rank.get(k, len(order)), k))
    rows: list[tuple[str, str]] = []
    for key in keys:
        if key not in before:
            rows.append(("+", f"{key} = {_toml_display(after[key])}"))
        elif key not in after:
            why = ("cleared" if key in rank
                   else "not walked at this layer; dropped")
            rows.append(("-", f"{key} = {_toml_display(before[key])}  "
                              f"({why})"))
        elif before[key] != after[key] or type(before[key]) is not type(
                after[key]):
            rows.append(("~", f"{key} = {_toml_display(before[key])} "
                              f"→ {_toml_display(after[key])}"))
    return rows


def review_and_write_config(ui: bale_wizard.WizardUI, cfg_path: Path, *,
                            existing: dict, new_cfg: dict, rendered: str,
                            layer: str) -> str:
    """Show what the walk changes in `cfg_path`, then write on confirm.

    The gate is the wizard's one write decision for bale.toml. Enter
    writes — so an Enter-through run lands the file exactly as the
    pre-review wizard did — and so does a closed stdin (scripted runs);
    only a typed n, or ^C at this prompt, leaves the file alone. A file
    whose bytes already equal the rendering is reported as unchanged and
    not rewritten (there is nothing a write could change).

    Returns the outcome for the closing summary: "created", "updated",
    "unchanged", or "not written".
    """
    from __main__ import log

    name = cfg_path.name
    on_disk: Optional[str] = None
    if cfg_path.is_file():
        try:
            on_disk = cfg_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            # load_config already parsed it, so this is unexpected; say so
            # and review as if the bytes differ (the write still asks).
            ui.warn(f"could not re-read {cfg_path} for the review: {e}",
                    indent=2)
            on_disk = ""

    rows = config_changes(existing, new_cfg, layer=layer)
    if on_disk is None:
        target = f"{cfg_path} (new file)"
        set_count = len(_flatten_config(new_cfg))
        verdict = (f"creates {name} with {set_count} key"
                   f"{'' if set_count == 1 else 's'} set" if set_count
                   else f"creates {name} with no keys set "
                        f"(only its header comment)")
        note = ""
    elif on_disk == rendered:
        ui.review(f"Review: {name}", target=str(cfg_path),
                  verdict="no changes: the file already matches the walk")
        log(f"{cfg_path} unchanged (already matches the walk)")
        return "unchanged"
    else:
        target = str(cfg_path)
        if rows:
            verdict = f"{len(rows)} change{'' if len(rows) == 1 else 's'}"
            note = ""
        else:
            verdict = "no value changes"
            note = ("The file is rewritten in the wizard's layout (header "
                    "comment, key order); every value stays the same.")
    ui.review(f"Review: {name}", target=target, verdict=verdict,
              changes=rows, note=note)

    if not ui.confirm(f"Write {name}?", default=True, eof=True,
                      interrupt=False):
        log(f"{cfg_path} not written (declined at the review)")
        ui.notice(f"{name} not written; the file on disk is unchanged.",
                  indent=2)
        return "not written"
    cfg_path.write_text(rendered, encoding="utf-8")
    log(f"wrote {cfg_path}")
    return "updated" if on_disk is not None else "created"


def walkthrough_baleignore(
        repo: Path, ui: Optional[bale_wizard.WizardUI] = None, *,
        suggestions: Optional[Sequence[bale_wizard.Alternative]] = None,
        ) -> None:
    """Walk the user through `<repo>/.baleignore` — the user-managed
    exclusion file the pack/apply pipelines read at BALE.md §6.4 / §11
    rule 14. Project-mode only; called from _cmd_config_init_project
    after the bale.toml step.

    The walk has four phases, each idempotent:

      1. If a `.baleignore` exists, walk its patterns one at a time —
         Enter keeps, n removes (default is keep).
      2. Prompt for additions, one per line, blank to finish.
      3. Review: the patterns removed and added versus the file on disk
         ("no changes" included).
      4. Write the file (or remove it, if the keep+add net is empty).
         When the review shows a change, a confirm gates the write —
         Enter (and a closed stdin) proceed, a typed n or ^C leaves the
         file alone; with no pattern change, the step proceeds as it
         always has, without asking.

    The file format: one pattern per line, blank lines and `#`-comments
    permitted. The walk preserves user-authored comments by passing them
    through verbatim in phase 1 (they're orientation for the patterns
    near them, and asking the user 'keep this comment?' for every comment
    would be noise). New patterns from phase 2 don't get auto-comments;
    the user is the canonical author of comments in this file.

    Syntax explanation is inline at the top of phase 2 so the user
    doesn't need to read BALE.md §6.4 to fill in a pattern. The phrasing
    matches what bin/bale's BaleignoreMatcher actually does — a single
    place where the supported subset is described to the user.

    Phase 2 also offers patterns drawn from what the repo actually holds
    (session wizard-defaults; baleignore_suggestions says which signals
    count), as numbered `[n] pattern  (count, size)` lines: typing a
    number at the add prompt adds that pattern, the same as typing it;
    one out of range is not a pick and re-asks (the checkpoint picker's
    rule). `suggestions` overrides the detection (tests pass their own;
    an empty sequence offers nothing). Patterns already kept are never
    offered, and a pick already added is not added twice. Enter still
    finishes, so an Enter-through run adds nothing.

    The function does not import bale (or its matcher) — keeps this
    module's circular-import surface minimal, and any pattern the user
    types here will be validated when pack/apply next loads the file.
    The cost of late validation is an error message at pack time
    instead of inline; the cost of a typo here is one re-run of
    `bale config init`, which is acceptable.
    """
    from __main__ import log

    ui = ui or bale_wizard.WizardUI()
    BALEIGNORE = ".baleignore"
    path = repo / BALEIGNORE

    ui.heading(BALEIGNORE, "patterns excluded from request tarballs")
    ui.table([("file", str(path))], indent=2)
    ui.emit("Applies on top of bale's baked-in exclusions and your "
            ".gitignore. bale reads this file when packing, and apply "
            "rejects a response whose changes touch a matched path "
            "(BALE.md §11 rule 14).", indent=2)

    existing_lines: list[str] = []
    if path.is_file():
        try:
            existing_lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as e:
            ui.warn(f"could not read {path}: {e}; skipping the .baleignore "
                    f"step.", indent=2)
            return
        ui.notice("Existing file: each pattern is walked to keep or "
                  "remove, then you can add more.", indent=2)
    else:
        ui.notice("No file yet; pressing Enter through skips creation.",
                  indent=2)

    # Phase 1: walk existing lines. Comments and blanks pass through
    # verbatim; pattern lines get a keep/remove. EOF/^C at any prompt is
    # interpreted as "keep" (consistent with the wizard's general bias
    # toward preservation on accidental aborts — the file is rewritten
    # only after the user finishes the walk).
    def _is_pattern(line: str) -> bool:
        stripped = line.strip()
        return bool(stripped) and not stripped.startswith("#")

    existing_patterns = [ln.strip() for ln in existing_lines
                         if _is_pattern(ln)]
    kept_lines: list[str] = []
    removed: list[str] = []
    position = 0
    for line in existing_lines:
        if not _is_pattern(line):
            # Pass through verbatim — these are the user's comments and
            # spacing, not patterns we walk.
            kept_lines.append(line)
            continue
        stripped = line.strip()
        position += 1
        ui.blank()
        ui.table([(f"pattern {position}/{len(existing_patterns)}",
                   stripped)], indent=2)
        raw = (ui.ask("keep? Enter keeps · n removes > ", indent=2)
               or "").lower()
        if raw in ("n", "no"):
            # Drop this line. Adjacent comment lines are preserved
            # above; the user may want to clean them up next run.
            removed.append(stripped)
            continue
        kept_lines.append(line)

    # Phase 2: prompt for additions. Show a brief syntax reminder so the
    # user doesn't need to read the spec.
    ui.blank()
    ui.emit("Add new patterns, one per line; an empty line finishes.",
            indent=2)
    ui.emit("Syntax (a subset of gitignore):", indent=2)
    ui.table([
        ("data/", "directory named 'data' anywhere"),
        ("/build/", "directory named 'build' at repo root only"),
        ("*.parquet", "files ending in .parquet, any depth"),
        ("src/legacy/", "that exact dir and everything under it"),
        ("src/legacy/*.vue", ".vue files directly in src/legacy/"),
    ], indent=4)
    ui.emit("Patterns starting with '!' (negation) are not supported.",
            indent=2)

    kept_patterns = [ln.strip() for ln in kept_lines if _is_pattern(ln)]
    if suggestions is None:
        found, why = baleignore_suggestions(repo, kept_patterns)
        if why:
            ui.emit(f"suggestions skipped: {why}", indent=2, style=("dim",))
    else:
        found = [alt for alt in suggestions
                 if alt.value.strip() not in kept_patterns]
    offered = bale_wizard.detected_first(found)
    if offered:
        ui.emit("Suggested from what this repo would ship (a number adds "
                "it):", indent=2)
        ui.alternatives(offered, indent=4, label="")
    picks = bale_wizard.pick_range(len(offered)) if offered else ""
    prompt = f"add · {picks} picks > " if offered else "add > "

    added: list[str] = []
    while True:
        raw = ui.ask(prompt, indent=2)
        if not raw:
            # Empty line finishes; EOF/^C (None) finishes too.
            break
        number = bale_wizard.pick_number(raw) if offered else None
        if number is not None:
            if not 1 <= number <= len(offered):
                ui.warn(f"no suggestion {number}; pick {picks}, type a "
                        f"pattern, or press Enter to finish.", indent=2)
                continue
            raw = offered[number - 1].value
            if raw in added:
                ui.notice(f"{raw} is already added.", indent=2)
                continue
            ui.notice(f"added {raw}", indent=2)
        if raw.startswith("!"):
            ui.warn(f"negation patterns aren't supported; skipping "
                    f"{bale_wizard.clip(raw)!r}", indent=2)
            continue
        added.append(raw)

    # Compose the new file body. If the user dropped every existing
    # pattern AND added nothing, remove the file rather than write a
    # noisy "all-comment" leftover. If only comments survived in the
    # kept-from-existing set and the user added nothing, also remove —
    # comments without patterns aren't load-bearing and a missing file
    # is the canonical "no .baleignore" state.
    new_pattern_lines = [ln for ln in kept_lines if _is_pattern(ln)] + added
    changes = ([("-", p) for p in removed] + [("+", p) for p in added])

    # Phase 3: review, before anything is written.
    if not new_pattern_lines:
        if path.is_file():
            ui.review(f"Review: {BALEIGNORE}", target=str(path),
                      verdict="removes the file: no patterns kept or added",
                      changes=changes)
            if not ui.confirm(f"Remove {BALEIGNORE}?", default=True,
                              eof=True, interrupt=False):
                log(f"{path} left in place (declined at the review)")
                ui.notice(f"{BALEIGNORE} left unchanged.", indent=2)
                return
            try:
                path.unlink()
                log(f"removed {path} (no patterns kept or added)")
                ui.notice(f"removed {BALEIGNORE}: no patterns active.",
                          indent=2)
            except OSError as e:
                # Surface the failure but don't abort the wizard — the
                # bale.toml step has already run by this point.
                ui.warn(f"could not remove {path}: {e}", indent=2)
        else:
            ui.review(f"Review: {BALEIGNORE}", target=str(path),
                      verdict="no changes")
            ui.notice("no .baleignore created: no patterns to write.",
                      indent=2)
        return

    if changes:
        count = len(changes)
        ui.review(f"Review: {BALEIGNORE}",
                  target=str(path) + ("" if path.is_file()
                                      else " (new file)"),
                  verdict=f"{count} pattern change{'' if count == 1 else 's'}",
                  changes=changes)
        if not ui.confirm(f"Write {BALEIGNORE}?", default=True, eof=True,
                          interrupt=False):
            log(f"{path} not written (declined at the review)")
            ui.notice(f"{BALEIGNORE} not written; the file on disk is "
                      f"unchanged.", indent=2)
            return
    else:
        ui.review(f"Review: {BALEIGNORE}", target=str(path),
                  verdict="no changes")

    # Phase 4: write. Compose by stitching together the kept lines (in
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
        ui.warn(f"could not write {path}: {e}", indent=2)
        return

    pattern_count = sum(1 for ln in body_lines if _is_pattern(ln))
    log(f"wrote {path} ({pattern_count} pattern(s))")
    ui.notice(f"wrote {BALEIGNORE} ({pattern_count} pattern(s) active).",
              indent=2)


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
    from __main__ import fail, refuse_system_dir, repo_root

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
    ui = bale_wizard.WizardUI()

    ui.title(
        "bale config init · project layer",
        rows=[("repo", str(repo)),
              ("config", f"{cfg_path} "
                         f"({'exists' if is_existing else 'new'})")],
        intro=("Canonical setup walkthrough for using bale on this repo. "
               "Idempotent: re-run any time to review or change. "
               "Everything past git identity is optional; pressing Enter "
               "through the rest leaves the repo in a perfectly usable "
               "state."))

    walkthrough_git_identity(repo, ui)

    wizard_grammar(ui, layer="project")
    suggestions = suggest_wizard_values("project", existing, repo=repo,
                                        config_path=cfg_path)
    new_cfg = walk_configurables(existing, layer="project",
                                 inherited=inherited, ui=ui, repo=repo,
                                 suggestions=suggestions)

    rendered = render_bale_toml(new_cfg, layer="project")
    outcome = review_and_write_config(
        ui, cfg_path, existing=existing, new_cfg=new_cfg, rendered=rendered,
        layer="project")

    # .baleignore walkthrough — project-mode only. The file lives at the
    # repo root and is the user-facing exclusion surface that pack and
    # apply consume (BALE.md §6.4, §11 rule 14). Visibility lives here
    # rather than in bin/bale's pack wizard because `bale config init` is
    # the canonical "set up bale for this project" surface — the user
    # who never runs `bale pack` interactively still configures here.
    walkthrough_baleignore(repo, ui)

    # Key information last: the paths touched, what was written, and how to
    # re-run — the summary sits nearest the prompt (the main-CLI output idiom).
    ui.heading("Done", "bale config init · project layer")
    ui.table([
        ("repo", str(repo)),
        ("config", f"{cfg_path} ({outcome})"),
        ("global", f"{GLOBAL_CONFIG_PATH} "
                   f"({'inherited' if GLOBAL_CONFIG_PATH.is_file() else 'not configured'})"),
    ], indent=2)
    ui.emit("Re-run `bale config init` any time to review or change.",
            indent=2)
    return 0


def _cmd_config_init_global() -> int:
    """Configure the global (install-layer) file at <install>/user/bale.toml.

    No git-identity walk: identity is a per-repo concern. No repo lookup:
    global config exists independently of any project; running this from
    outside any git repo is fine. Refuses system dirs out of caution
    (cwd parity with project mode), even though we don't read cwd otherwise.
    """
    from __main__ import refuse_system_dir

    cwd = Path.cwd().resolve()
    refuse_system_dir(cwd)

    cfg_path = GLOBAL_CONFIG_PATH
    existing = load_global_config()
    is_existing = cfg_path.is_file()
    ui = bale_wizard.WizardUI()

    # Create the user/ subtree on first write. Idempotent: exist_ok=True.
    # parents=True covers the (theoretical) case where install root exists
    # but user/ has been deleted manually.
    GLOBAL_USER_DIR.mkdir(parents=True, exist_ok=True)

    ui.title(
        "bale config init --global · install layer",
        rows=[("install", str(INSTALL_ROOT)),
              ("config", f"{cfg_path} "
                         f"({'exists' if is_existing else 'new'})")],
        intro=("Configures the install-wide global layer for this bale "
               "install. Every project that runs this bale inherits these "
               "defaults; each project's own bale.toml can override "
               "per-key. Hook scripts referenced here live under "
               "<install>/user/scripts/ and are preserved across upgrades "
               "(via `upgrade.sh`). Idempotent: re-run any time to review "
               "or change."))

    wizard_grammar(ui, layer="global")
    # No inherited layer below global.
    suggestions = suggest_wizard_values("global", existing,
                                        config_path=cfg_path)
    new_cfg = walk_configurables(existing, layer="global", inherited=None,
                                 ui=ui, suggestions=suggestions)

    rendered = render_bale_toml(new_cfg, layer="global")
    outcome = review_and_write_config(
        ui, cfg_path, existing=existing, new_cfg=new_cfg, rendered=rendered,
        layer="global")

    # Key information last (same idiom as project mode): install + config
    # paths, what was written, the scripts dir, and how to re-run.
    ui.heading("Done", "bale config init --global")
    ui.table([
        ("install", str(INSTALL_ROOT)),
        ("config", f"{cfg_path} ({outcome})"),
        ("scripts dir", f"{GLOBAL_USER_DIR / 'scripts'} "
                        f"(place global hook scripts here)"),
    ], indent=2)
    ui.emit("Re-run `bale config init --global` any time to review or "
            "change.", indent=2)
    return 0


# ---------------------------------------------------------------------------
# 4. `bale config hooks` — the acceptance store view (v0.4.29, board 83)
# ---------------------------------------------------------------------------
#
# The store (section 2's trio) was auditable — a JSON file a human can
# read — but not operable: "forget this script" meant hand-editing JSON.
# This verb is the operable face. Bare, it lists every entry; --forget
# removes exactly one and says what it removed. No --forget-all, by
# desk ruling: forgetting is per-script, and deleting the file is the
# honest spelling of "forget everything".
#
# --json follows the process-wide stream discipline bale_report owns
# (enable_json_mode / emit_json_line): stdout carries exactly the one
# report line, everything else — the `[bale] ` trail and the human block
# — goes to stderr. The renderer (bale_report.format_config_hooks_json)
# lives beside its siblings since v0.4.31 (board 89) — it sat here for
# one release only because bale_report was another open session's
# forecast the sitting it landed; the outcome vocabulary below stays
# here, with the verb that speaks it.

# Outcome vocabulary for the --json report, and for the human block's
# verb. Error paths exit through fail() (stderr, non-zero, nothing on
# stdout), like status.
CONFIG_HOOKS_OUTCOME_LISTED = "listed"
CONFIG_HOOKS_OUTCOME_FORGOTTEN = "forgotten"


def _acceptance_entry_view(key: str, value) -> dict:
    """One store entry as the report and the listing see it: the full
    sha256 plus the four documented fields, each None when a hand-edited
    store lacks it or holds a non-string, and a `malformed` flag when the
    value is not even an object — displayed, never dropped, so the
    listing shows what the file actually contains."""
    view = {"sha256": key}
    if isinstance(value, dict):
        for field_name in _ACCEPTANCE_KEYS:
            raw = value.get(field_name)
            view[field_name] = raw if isinstance(raw, str) else None
        view["malformed"] = False
    else:
        for field_name in _ACCEPTANCE_KEYS:
            view[field_name] = None
        view["malformed"] = True
    return view


def _acceptance_entries_sorted(data: dict) -> list[dict]:
    """Every entry, oldest acceptance first (ties and missing timestamps
    fall back to key order), so the listing reads as a history."""
    views = [_acceptance_entry_view(k, v) for k, v in data.items()]
    views.sort(key=lambda e: (e["accepted_at"] or "", e["sha256"]))
    return views


def _print_acceptance_listing(store: Path, entries: list[dict]) -> None:
    """The human block: one entry per two lines — identity row, then the
    script path indented beneath it — so a long absolute path never
    pushes the hook/layer/time columns off the terminal."""
    n = len(entries)
    if not store.is_file():
        print(f"  no hook acceptances remembered at {store}")
        print("  (nothing accepted yet — the file is created by the first "
              "interactive accept of a project or configured hook)")
        return
    if n == 0:
        print(f"  no hook acceptances remembered at {store}")
        print("  (the file exists but holds no entries — if a `[bale] ` "
              "warning printed above, it is malformed and the prompt is "
              "treating it as empty too)")
        return
    print(f"  {n} hook acceptance{'s' if n != 1 else ''} remembered at "
          f"{store}")
    print(f"  {'sha256 (prefix)':<16} {'hook':<18} {'layer':<11} accepted at")
    for e in entries:
        if e["malformed"]:
            print(f"  {e['sha256'][:12]}…    (malformed entry — not an "
                  f"object; fix or --forget it)")
            continue
        print(f"  {e['sha256'][:12]}…    {e['hook'] or '?':<18} "
              f"{e['layer'] or '?':<11} {e['accepted_at'] or '?'}")
        print(f"      {e['script'] or '? (no script path recorded)'}")


def cmd_config_hooks(args: argparse.Namespace) -> int:
    """`bale config hooks [--forget SHA256-OR-PREFIX] [--json]`.

    Needs no git repo: the store is install-level. Refuses system dirs
    for cwd parity with `config init --global`. Every refusal goes
    through fail() — stderr, exit 1, nothing on stdout — so a --json
    consumer never has to parse a half-report.
    """
    from __main__ import VERSION, fail, log, refuse_system_dir
    import bale_report  # sibling on sys.path (bin/), like _bale_toml

    if getattr(args, "json", False):
        # Stream discipline first, before any line can print (matches
        # cmd_status / cmd_unlock): the swap routes every print() and
        # log() below to stderr; emit_json_line reaches the real stdout.
        bale_report.enable_json_mode()

    cwd = Path.cwd().resolve()
    refuse_system_dir(cwd)

    store = HOOK_ACCEPTANCES_PATH
    forgotten: Optional[dict] = None
    prefix = getattr(args, "forget", None)
    if prefix is not None:
        try:
            key, removed = forget_hook_acceptance(prefix, store)
        except ValueError as e:
            fail(f"config hooks --forget: {e}")
        except HookAcceptanceLookupError as e:
            if e.kind == "ambiguous":
                data = load_hook_acceptances(store)
                lines = "\n".join(
                    f"  {k}  ({_acceptance_entry_view(k, data[k])['hook'] or '?'}"
                    f", {_acceptance_entry_view(k, data[k])['script'] or '?'})"
                    for k in e.matches)
                fail(f"config hooks --forget: prefix {e.prefix!r} is "
                     f"ambiguous — it starts {len(e.matches)} remembered "
                     f"sha256s:\n{lines}\nGive more characters, or the full "
                     f"sha256.")
            fail(f"config hooks --forget: no remembered hook acceptance "
                 f"starts with {e.prefix!r} in {store}. `bale config hooks` "
                 f"lists what is remembered.")
        except OSError as e:
            fail(f"config hooks --forget: could not rewrite {store} ({e}); "
                 f"nothing was removed.")
        forgotten = _acceptance_entry_view(key, removed)
        log(f"config hooks: forgot sha256 {key[:12]}… "
            f"({forgotten['hook'] or '?'}, {forgotten['layer'] or '?'}, "
            f"{forgotten['script'] or '?'}) from {store} — that script's "
            f"prompt defaults decline again until accepted anew")

    data = load_hook_acceptances(store)
    entries = _acceptance_entries_sorted(data)

    print()
    if forgotten is not None:
        print("bale config hooks --forget — done")
        print(f"  forgot:  {forgotten['sha256']}")
        print(f"           hook {forgotten['hook'] or '?'}, layer "
              f"{forgotten['layer'] or '?'}, accepted "
              f"{forgotten['accepted_at'] or '?'}")
        print(f"           {forgotten['script'] or '? (no script path recorded)'}")
        print("  remaining:")
    else:
        print("bale config hooks")
    _print_acceptance_listing(store, entries)

    if getattr(args, "json", False):
        bale_report.emit_json_line(bale_report.format_config_hooks_json(
            outcome=(CONFIG_HOOKS_OUTCOME_FORGOTTEN if forgotten is not None
                     else CONFIG_HOOKS_OUTCOME_LISTED),
            version=VERSION, store=store, entries=entries,
            forgotten=forgotten))
    return 0
