#!/usr/bin/env python3
"""
Claudia: claudia-next-steps.py
Stop hook that suggests next actions after Claude completes something.
Advisory only (exit 0 with additionalContext), never blocks.
Gate: beginner only. Max 3 suggestion moments per session.
"""

import json
import os
import re
import sys
import time

# Completion signals
COMPLETION_PATTERNS = [
    r"I've created",
    r"I have created",
    r"I've written",
    r"I've built",
    r"I've set up",
    r"I've added",
    r"I've updated",
    r"I've fixed",
    r"I've implemented",
    r"Done[.!]",
    r"Here's your",
    r"Here is your",
    r"All set[.!]",
    r"That's done",
    r"It's ready",
    r"The [\w\s]+ is ready",
    r"Your [\w\s]+ is ready",
]

# File type -> contextual next steps
NEXT_STEPS = {
    "html": [
        "Open it in your browser to see it: `open {filename}`",
        "Try changing some text in the file and refreshing",
        "Ask me to add CSS styling: 'make it look better'",
    ],
    "css": [
        "Refresh your browser to see the changes",
        "Ask me to add more styles: 'add a dark mode'",
    ],
    "py": [
        "Run it: `python3 {filename}`",
        "Ask me to add error handling or tests",
        "Try changing the inputs and running again",
    ],
    "js": [
        "Run it: `node {filename}`",
        "Ask me to explain how it works: `/claudia:explain {filename}`",
        "Try modifying it and see what happens",
    ],
    "jsx": [
        "Start the dev server: `npm run dev` or `npm start`",
        "Ask me to add more components",
        "Check it in your browser at localhost",
    ],
    "tsx": [
        "Start the dev server: `npm run dev` or `npm start`",
        "Ask me to add more components",
        "Check it in your browser at localhost",
    ],
    "json": [
        "Run `npm install` to install dependencies",
        "Check the scripts with `npm run`",
    ],
    "default": [
        "Ask me to explain what I built: `/claudia:explain`",
        "Ask me to review it for issues: `/claudia:review`",
        "Tell me what you want to add or change next",
    ],
}

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


# Pattern to extract filenames from the message
FILENAME_PATTERN = r"[`'\"]?(\S+\.(\w{1,4}))[`'\"]?"


def get_state_file(session_id):
    return os.path.expanduser(f"~/.claude/claudia_nextsteps_state_{session_id}.json")


def load_state(session_id):
    state_file = get_state_file(session_id)
    if os.path.exists(state_file):
        try:
            with open(state_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"count": 0}
    return {"count": 0}


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
    _, experience = load_user_config()
    return experience


def check(input_data, proactivity, experience):
    """Run next-steps logic. Returns output dict or None."""
    session_id = input_data.get("session_id", "default")
    message = input_data.get("last_assistant_message", "")

    if not message:
        return None

    if experience != "beginner":
        return None

    state = load_state(session_id)

    if state["count"] >= 3:
        return None

    is_completion = any(
        re.search(pattern, message, re.IGNORECASE)
        for pattern in COMPLETION_PATTERNS
    )

    if not is_completion:
        return None

    # Find mentioned files to determine context
    file_matches = re.findall(FILENAME_PATTERN, message)
    ext = None
    filename = None
    for fname, fext in file_matches:
        fext = fext.lower()
        if fext in NEXT_STEPS:
            ext = fext
            filename = fname
            break

    if ext and ext in NEXT_STEPS:
        steps = NEXT_STEPS[ext]
    else:
        steps = NEXT_STEPS["default"]

    formatted = []
    for step in steps[:3]:
        if filename:
            formatted.append(step.format(filename=filename))
        else:
            formatted.append(step.replace(" {filename}", "").replace("{filename}", "the file"))

    state["count"] += 1
    save_state(session_id, state)

    suggestion_text = "Claudia: What's next? Here are some ideas:\n" + "\n".join(
        f"  - {step}" for step in formatted
    )
    return {
        "additionalContext": suggestion_text,
        "systemMessage": f"\033[38;5;160m{suggestion_text}\033[0m",
    }


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
