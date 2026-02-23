#!/usr/bin/env python3
"""
Claudia: claudia-milestones.py
Stop hook that celebrates beginner milestones.
Advisory only (exit 0 with additionalContext), never blocks.
Gate: beginner only. Persistent state (cross-session).
"""

import json
import os
import re
import sys
import time

# Milestone definitions: key, detection pattern, celebration message
MILESTONES = {
    "first_file": {
        "patterns": [
            r"(?:I've |I have )?(?:created|wrote|written|saved|generated)\s+[`'\"]?\S+\.\w+",
            r"(?:new file|writing to|saved to)\s+[`'\"]?\S+\.\w+",
        ],
        "message": "You just created your first file. That's real code in the real world.",
    },
    "first_error_fixed": {
        "patterns": [
            r"(?:I've |I have )?(?:fixed|resolved|corrected|patched)\s+(?:the |this |that )?(?:error|bug|issue|problem)",
            r"(?:error|bug|issue) (?:is |has been )?(?:fixed|resolved|corrected)",
            r"should (?:work|be fixed) now",
        ],
        "message": "First bug squashed. Welcome to the club.",
    },
    "first_commit": {
        "patterns": [
            r"(?:I've |I have )?(?:committed|created a commit|made a commit)",
            r"git commit",
            r"committed (?:the |your )?changes",
        ],
        "message": "First commit. Your code has a save point now.",
    },
    "first_project_run": {
        "patterns": [
            r"(?:server|app|application|project) (?:is )?running",
            r"(?:running|started) (?:on|at) (?:http|localhost|port)",
            r"npm (?:run )?(?:dev|start)",
            r"python3?\s+\S+\.py",
            r"node\s+\S+\.js",
        ],
        "message": "Your project is running. You built something that works.",
    },
    "ten_files": {
        "patterns": [],  # Special detection: count file mentions
        "message": "10+ files. This isn't a toy -- it's a real project.",
    },
}

STATE_FILE = os.path.expanduser("~/.claude/claudia-milestones.json")


def stop_lock_acquire(session_id):
    """Try to acquire the per-turn Stop hook lock. Returns True if acquired."""
    lock_file = os.path.expanduser(f"~/.claude/claudia_stop_lock_{session_id}.tmp")
    now = time.time()
    try:
        if os.path.exists(lock_file):
            with open(lock_file) as f:
                ts = float(f.read().strip())
            if now - ts < 2.0:
                return False  # Another hook already claimed this turn
        os.makedirs(os.path.dirname(lock_file), exist_ok=True)
        with open(lock_file, "w") as f:
            f.write(str(now))
        return True
    except (IOError, ValueError):
        return True  # On error, let it through


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"achieved": [], "file_count": 0}
    return {"achieved": [], "file_count": 0}


def save_state(state):
    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except IOError:
        pass


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from claudia_config import load_user_config, dismiss_hint


def load_config():
    _, experience = load_user_config()
    return experience


def count_new_files(message):
    """Count file creation mentions in the message."""
    patterns = [
        r"(?:created|wrote|written|saved|generated)\s+[`'\"]?(\S+\.\w+)",
        r"(?:new file|writing to|saved to)\s+[`'\"]?(\S+\.\w+)",
    ]
    files = set()
    for pattern in patterns:
        for match in re.finditer(pattern, message, re.IGNORECASE):
            files.add(match.group(1))
    return len(files)


def check(input_data, proactivity, experience):
    """Run milestones logic. Returns output dict or None."""
    message = input_data.get("last_assistant_message", "")

    if not message:
        return None

    if experience != "beginner":
        return None

    state = load_state()
    achieved = set(state.get("achieved", []))
    celebration = None

    # Track file count for ten_files milestone
    new_files = count_new_files(message)
    if new_files > 0:
        state["file_count"] = state.get("file_count", 0) + new_files

    # Check ten_files milestone
    if "ten_files" not in achieved and state.get("file_count", 0) >= 10:
        achieved.add("ten_files")
        celebration = MILESTONES["ten_files"]["message"]

    # Check pattern-based milestones (first match wins)
    if not celebration:
        for key, milestone in MILESTONES.items():
            if key in achieved or key == "ten_files":
                continue
            for pattern in milestone["patterns"]:
                if re.search(pattern, message, re.IGNORECASE):
                    achieved.add(key)
                    celebration = milestone["message"]
                    break
            if celebration:
                break

    if celebration:
        state["achieved"] = list(achieved)
        save_state(state)
        msg = f"Claudia: {celebration}"
        user_hint, claude_hint = dismiss_hint("milestones")
        return {"additionalContext": msg + "\n" + claude_hint, "systemMessage": f"\033[38;5;160m{msg}\n{user_hint}\033[0m"}

    # Save state even without celebration (for file_count tracking)
    if new_files > 0:
        save_state(state)

    return None


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)

    _, experience = load_user_config()
    session_id = input_data.get("session_id", "default")
    result = check(input_data, None, experience)
    if result and stop_lock_acquire(session_id):
        print(json.dumps(result))

    sys.exit(0)


if __name__ == "__main__":
    main()
