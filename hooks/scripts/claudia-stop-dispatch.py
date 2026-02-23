#!/usr/bin/env python3
"""
Claudia: claudia-stop-dispatch.py
Single dispatcher for all Stop hooks. Runs milestones, run-suggest,
next-steps, and teach in one process instead of 4 subprocesses.
First hook with output wins.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from claudia_config import load_user_config, load_suppress_topics

# Import check() from each Stop hook module
import importlib

def _import_hook(name):
    """Import a hook module by filename (without .py)."""
    return importlib.import_module(name.replace("-", "_").replace(".py", ""))

# Hook execution order (matches original hooks.json order)
HOOK_MODULES = [
    "claudia-milestones",
    "claudia-run-suggest",
    "claudia-next-steps",
    "claudia-teach",
]


def stop_lock_acquire(session_id):
    """Try to acquire the per-turn Stop hook lock. Returns True if acquired."""
    lock_file = os.path.expanduser(f"~/.claude/claudia_stop_lock_{session_id}.tmp")
    now = time.time()
    try:
        if os.path.exists(lock_file):
            with open(lock_file) as f:
                ts = float(f.read().strip())
            if now - ts < 2.0:
                return False
        os.makedirs(os.path.dirname(lock_file), exist_ok=True)
        with open(lock_file, "w") as f:
            f.write(str(now))
        return True
    except (IOError, ValueError):
        return True


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)

    session_id = input_data.get("session_id", "default")
    proactivity, experience = load_user_config()
    input_data["suppress_topics"] = load_suppress_topics()

    # Try each hook in order; first with output wins
    for module_name in HOOK_MODULES:
        try:
            mod = _import_hook(module_name)
            result = mod.check(input_data, proactivity, experience)
            if result:
                if stop_lock_acquire(session_id):
                    print(json.dumps(result))
                sys.exit(0)
        except Exception:
            # Don't let one broken hook kill the others
            continue

    sys.exit(0)


if __name__ == "__main__":
    main()
