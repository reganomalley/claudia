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


def load_config():
    experience = "intermediate"
    context_path = os.path.expanduser("~/.claude/claudia-context.json")
    if os.path.exists(context_path):
        try:
            with open(context_path) as f:
                data = json.load(f)
                experience = data.get("experience", experience)
        except (json.JSONDecodeError, IOError):
            pass
    return experience


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)

    session_id = input_data.get("session_id", "default")
    message = input_data.get("last_assistant_message", "")

    if not message:
        sys.exit(0)

    experience = load_config()

    # Gate: beginner only
    if experience != "beginner":
        sys.exit(0)

    state = load_state(session_id)

    # Max 3 suggestion moments per session
    if state["count"] >= 3:
        sys.exit(0)

    # Check for completion signals
    is_completion = any(
        re.search(pattern, message, re.IGNORECASE)
        for pattern in COMPLETION_PATTERNS
    )

    if not is_completion:
        sys.exit(0)

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

    # Get appropriate next steps
    if ext and ext in NEXT_STEPS:
        steps = NEXT_STEPS[ext]
    else:
        steps = NEXT_STEPS["default"]

    # Format steps with filename if available
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
    output = json.dumps({"additionalContext": suggestion_text})
    print(output)
    sys.exit(0)


if __name__ == "__main__":
    main()
