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


def load_config():
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

    context_path = os.path.expanduser("~/.claude/claudia-context.json")
    if os.path.exists(context_path):
        try:
            with open(context_path) as f:
                data = json.load(f)
                experience = data.get("experience", experience)
        except (json.JSONDecodeError, IOError):
            pass

    return proactivity, experience


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
        shown_types.add("package.json")
        state["shown_types"] = list(shown_types)
        save_state(session_id, state)
        suggestion = RUN_SUGGESTIONS["package.json"][1]
        msg = f"Claudia: {suggestion}"
        output = json.dumps({"additionalContext": msg, "systemMessage": msg})
        print(output)
        sys.exit(0)

    # Check for file creation patterns
    for pattern in FILE_PATTERNS:
        matches = re.finditer(pattern, message, re.IGNORECASE)
        for match in matches:
            filename = match.group(1)
            ext = match.group(2).lower()
            if ext in RUN_SUGGESTIONS and ext not in shown_types:
                shown_types.add(ext)
                state["shown_types"] = list(shown_types)
                save_state(session_id, state)
                suggestion = RUN_SUGGESTIONS[ext][1].format(filename=filename)
                msg = f"Claudia: {suggestion}"
                output = json.dumps({"additionalContext": msg, "systemMessage": msg})
                print(output)
                sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
