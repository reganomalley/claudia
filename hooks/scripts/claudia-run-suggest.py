#!/usr/bin/env python3
"""
Claudia: claudia-run-suggest.py
Stop hook that suggests how to run files Claude just created.
Advisory only (exit 0 with additionalContext), never blocks.
Gate: beginner OR high proactivity. Session dedup by file type.
"""

import json
import os
import re
import sys
import time

# File type -> run suggestion
RUN_SUGGESTIONS = {
    "html": ('open {filename}', "Want to see it? `open {filename}`"),
    "py": ('python3 {filename}', "Run it: `python3 {filename}`"),
    "js": ('node {filename}', "Run it: `node {filename}`"),
    "ts": ('npx tsx {filename}', "Run it: `npx tsx {filename}`"),
    "sh": ('bash {filename}', "Run it: `bash {filename}`"),
    "package.json": ('npm install', "Install deps: `npm install`"),
}

# Patterns that indicate file creation/writing
FILE_PATTERNS = [
    r"(?:I've |I have )?(?:created|wrote|written|saved|generated|made)\s+[`'\"]?(\S+\.(\w+))[`'\"]?",
    r"(?:File|Created|Wrote|Saved)\s+[`'\"]?(\S+\.(\w+))[`'\"]?",
    r"(?:new file|writing to|saved to)\s+[`'\"]?(\S+\.(\w+))[`'\"]?",
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


PACKAGE_JSON_PATTERN = r"(?:created|wrote|updated|modified)\s+[`'\"]?package\.json[`'\"]?"


def get_state_file(session_id):
    return os.path.expanduser(f"~/.claude/claudia_runsuggest_state_{session_id}.json")


def load_state(session_id):
    state_file = get_state_file(session_id)
    if os.path.exists(state_file):
        try:
            with open(state_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"shown_types": []}
    return {"shown_types": []}


def save_state(session_id, state):
    state_file = get_state_file(session_id)
    try:
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, "w") as f:
            json.dump(state, f)
    except IOError:
        pass


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from claudia_config import load_user_config


def load_config():
    return load_user_config()


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)

    session_id = input_data.get("session_id", "default")
    message = input_data.get("last_assistant_message", "")

    if not message:
        sys.exit(0)

    proactivity, experience = load_config()
    is_beginner = experience == "beginner"

    # Gate: beginner OR high proactivity
    if not is_beginner and proactivity != "high":
        sys.exit(0)

    state = load_state(session_id)
    shown_types = set(state.get("shown_types", []))

    # Check for package.json mentions
    if "package.json" not in shown_types and re.search(PACKAGE_JSON_PATTERN, message, re.IGNORECASE):
        if not stop_lock_acquire(session_id):
            sys.exit(0)
        shown_types.add("package.json")
        state["shown_types"] = list(shown_types)
        save_state(session_id, state)
        suggestion = RUN_SUGGESTIONS["package.json"][1]
        msg = f"Claudia: {suggestion}"
        output = json.dumps({"additionalContext": msg, "systemMessage": f"\033[38;5;209m{msg}\033[0m"})
        print(output)
        sys.exit(0)

    # Check for file creation patterns
    for pattern in FILE_PATTERNS:
        matches = re.finditer(pattern, message, re.IGNORECASE)
        for match in matches:
            filename = match.group(1)
            ext = match.group(2).lower()
            if ext in RUN_SUGGESTIONS and ext not in shown_types:
                if not stop_lock_acquire(session_id):
                    sys.exit(0)
                shown_types.add(ext)
                state["shown_types"] = list(shown_types)
                save_state(session_id, state)
                suggestion = RUN_SUGGESTIONS[ext][1].format(filename=filename)
                msg = f"Claudia: {suggestion}"
                output = json.dumps({"additionalContext": msg, "systemMessage": f"\033[38;5;209m{msg}\033[0m"})
                print(output)
                sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
