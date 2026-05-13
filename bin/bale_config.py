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
  2. Configurables: load and merge                    (~line 115)
  3. `bale config init` wizard                        (~line 320)

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
import tomllib
from pathlib import Path
from typing import Optional


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
    # List of directories to search when `bale apply` or `bale retry`
    # receives a relative tarball name. Tried in order; first match wins.
    # Absolute paths bypass search entirely.
    "search_paths",
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

    # [apply] — list-shaped keys, replace semantics. Pass values through
    # untouched; get_apply_search_paths handles expansion + strict shape
    # checking at read time.
    g_apply = g.get("apply") if isinstance(g.get("apply"), dict) else {}
    p_apply = p.get("apply") if isinstance(p.get("apply"), dict) else {}
    out_apply: dict = {}
    if "search_paths" in p_apply:
        out_apply["search_paths"] = p_apply["search_paths"]
    elif "search_paths" in g_apply:
        out_apply["search_paths"] = g_apply["search_paths"]
    if out_apply:
        merged["apply"] = out_apply

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
            "Directories `bale apply` and `bale retry` search when given a",
            "relative tarball name. Tried in order; first match wins. An",
            "absolute path argument bypasses search. Cwd is always tried",
            "first implicitly — you don't need to list it.",
            "Tilde (~/Downloads) and env vars ($HOME/Downloads) expand at",
            "use time, so the committed file stays portable across machines.",
            "Use case: a `post_pack` hook drops the request tarball in",
            "~/Downloads; with ~/Downloads in search_paths, the matching",
            "`bale apply request-NNN.tar.gz` works from anywhere in the repo.",
        ],
    )
    if val_list is not None:
        # Both the value-set case and the empty-list (suppress) case go in;
        # the renderer emits search_paths = [...] either way.
        new.setdefault("apply", {})["search_paths"] = val_list

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
        parts.append("")

    return "\n".join(parts)


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
    print(f"bale config init (project layer)")
    print(f"  repo:    {repo}")
    print(f"  config:  {cfg_path}")
    if GLOBAL_CONFIG_PATH.is_file():
        print(f"  global:  {GLOBAL_CONFIG_PATH} (inherited)")
    else:
        print(f"  global:  {GLOBAL_CONFIG_PATH} (not configured)")
    if is_existing:
        print(f"  (existing file; current values shown, Enter keeps each.)")
    else:
        print(f"  (new file; only the keys you set will be written.)")
    print()
    print(f"  This is the canonical setup walkthrough for using bale on this")
    print(f"  repo. It's idempotent — re-run any time to review or change.")
    print(f"  Everything past git identity is optional; pressing Enter through")
    print(f"  the rest leaves the repo in a perfectly usable state.")

    walkthrough_git_identity(repo)

    print()
    print("Configurables (project layer)")
    new_cfg = walk_configurables(existing, layer="project", inherited=inherited)

    rendered = render_bale_toml(new_cfg, layer="project")
    cfg_path.write_text(rendered, encoding="utf-8")
    log(f"wrote {cfg_path}")

    print()
    print(f"  bale.toml: {cfg_path}")
    print(f"  Re-run `bale config init` any time to review or change.")
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
    print(f"bale config init --global")
    print(f"  install: {INSTALL_ROOT}")
    print(f"  config:  {cfg_path}")
    if is_existing:
        print(f"  (existing file; current values shown, Enter keeps each.)")
    else:
        print(f"  (new file; only the keys you set will be written.)")
    print()
    print(f"  Configures the install-wide global layer for this bale install.")
    print(f"  Every project that runs this bale inherits these defaults; each")
    print(f"  project's own bale.toml can override per-key.")
    print(f"  Hook scripts referenced here live under <install>/user/scripts/")
    print(f"  and are preserved across upgrades (via `upgrade.sh`).")
    print(f"  It's idempotent — re-run any time to review or change.")

    print()
    print("Configurables (global layer)")
    # No inherited layer below global.
    new_cfg = walk_configurables(existing, layer="global", inherited=None)

    rendered = render_bale_toml(new_cfg, layer="global")
    cfg_path.write_text(rendered, encoding="utf-8")
    log(f"wrote {cfg_path}")

    print()
    print(f"  bale.toml (global): {cfg_path}")
    print(f"  scripts dir:        {GLOBAL_USER_DIR / 'scripts'} (place global hook scripts here)")
    print(f"  Re-run `bale config init --global` any time to review or change.")
    return 0
