#!/usr/bin/env python3
"""
Claudia: claudia_config.py
Shared configuration module for all Claudia hooks.
Handles project resolution, user config, and project-scoped context.
"""

import hashlib
import json
import os
from datetime import datetime, timezone

# --- Project Resolution ---

def resolve_project():
    """Walk up from cwd looking for .git to find the project root.

    Returns:
        (key, path) where key is md5[:8] of the resolved path,
        or (None, None) if cwd is ~ or no .git found.
    """
    home = os.path.expanduser("~")
    cwd = os.getcwd()

    # At home directory: no project
    if os.path.realpath(cwd) == os.path.realpath(home):
        return (None, None)

    # Walk up looking for .git
    current = cwd
    while True:
        if os.path.isdir(os.path.join(current, ".git")):
            key = hashlib.md5(current.encode()).hexdigest()[:8]
            return (key, current)
        parent = os.path.dirname(current)
        if parent == current:
            break
        # Don't go above home
        if os.path.realpath(parent) == os.path.realpath(home):
            break
        current = parent

    # No .git found: use cwd as root (but not home)
    key = hashlib.md5(cwd.encode()).hexdigest()[:8]
    return (key, cwd)


# --- User Config ---

def load_suppress_topics():
    """Load suppress_topics list from ~/.claude/claudia.json.

    Returns:
        list of topic strings to suppress (empty if not set or file missing).
    """
    config_path = os.path.expanduser("~/.claude/claudia.json")
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                data = json.load(f)
                topics = data.get("suppress_topics", [])
                if isinstance(topics, list):
                    return topics
        except (json.JSONDecodeError, IOError):
            pass
    return []


def load_user_config():
    """Load proactivity from ~/.claude/claudia.json, experience from context.

    Returns:
        (proactivity, experience) tuple with string values.
        Defaults: ("moderate", "intermediate")
    """
    proactivity = "moderate"
    experience = "intermediate"

    config_path = os.path.expanduser("~/.claude/claudia.json")
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                data = json.load(f)
                proactivity = data.get("proactivity", proactivity)
        except (json.JSONDecodeError, IOError):
            pass

    # Experience comes from project context (tries project-scoped first, then global)
    ctx = load_project_context()
    experience = ctx.get("experience", experience)

    return proactivity, experience


# --- Project Context ---

def _projects_dir():
    return os.path.expanduser("~/.claude/claudia-projects")


def _project_file(key):
    return os.path.join(_projects_dir(), f"{key}.json")


def _registry_path():
    return os.path.expanduser("~/.claude/claudia-projects.json")


def _global_context_path():
    return os.path.expanduser("~/.claude/claudia-context.json")


def load_project_context(key=None):
    """Load project-scoped context, falling back to global claudia-context.json.

    Args:
        key: Project key. If None, auto-resolves from cwd.

    Returns:
        dict with project context (stack, decisions, experience, etc.)
    """
    if key is None:
        key, _ = resolve_project()

    # Try project-specific file first
    if key:
        pfile = _project_file(key)
        if os.path.exists(pfile):
            try:
                with open(pfile) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

    # Fall back to global context
    global_path = _global_context_path()
    if os.path.exists(global_path):
        try:
            with open(global_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    return {}


def save_project_context(data, key=None, path=None):
    """Save project-scoped context and update the registry.

    Args:
        data: dict of context to save (merged with existing)
        key: Project key. If None, auto-resolves from cwd.
        path: Project path. If None, auto-resolves from cwd.
    """
    if key is None or path is None:
        resolved_key, resolved_path = resolve_project()
        key = key or resolved_key
        path = path or resolved_path

    if not key:
        # No project resolved (at home dir) -- write to global
        global_path = _global_context_path()
        existing = {}
        if os.path.exists(global_path):
            try:
                with open(global_path) as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        existing.update(data)
        try:
            os.makedirs(os.path.dirname(global_path), exist_ok=True)
            with open(global_path, "w") as f:
                json.dump(existing, f, indent=2)
        except IOError:
            pass
        return

    # Write project-specific file
    pfile = _project_file(key)
    existing = {}
    if os.path.exists(pfile):
        try:
            with open(pfile) as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    existing.update(data)
    existing["project_key"] = key
    if path:
        existing["path"] = path
    if "name" not in existing and path:
        existing["name"] = os.path.basename(path)

    try:
        os.makedirs(os.path.dirname(pfile), exist_ok=True)
        with open(pfile, "w") as f:
            json.dump(existing, f, indent=2)
    except IOError:
        pass

    # Update registry
    _update_registry(key, existing.get("name", os.path.basename(path or "")), path)


def _update_registry(key, name, path):
    """Update the project registry with this project's info."""
    registry = load_registry()
    now = datetime.now(timezone.utc).isoformat()

    if key in registry["projects"]:
        registry["projects"][key]["last_active"] = now
        if name:
            registry["projects"][key]["name"] = name
        if path:
            registry["projects"][key]["path"] = path
    else:
        registry["projects"][key] = {
            "name": name or "",
            "path": path or "",
            "last_active": now,
            "created": now,
        }

    try:
        rpath = _registry_path()
        os.makedirs(os.path.dirname(rpath), exist_ok=True)
        with open(rpath, "w") as f:
            json.dump(registry, f, indent=2)
    except IOError:
        pass


def load_registry():
    """Load the project registry.

    Returns:
        dict with "version" and "projects" keys.
    """
    rpath = _registry_path()
    if os.path.exists(rpath):
        try:
            with open(rpath) as f:
                data = json.load(f)
                if isinstance(data, dict) and "projects" in data:
                    return data
        except (json.JSONDecodeError, IOError):
            pass
    return {"version": 1, "projects": {}}
