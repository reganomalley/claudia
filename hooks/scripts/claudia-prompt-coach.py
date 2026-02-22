#!/usr/bin/env python3
"""
Claudia: claudia-prompt-coach.py
UserPromptSubmit hook that fires before Claude processes a user message.
Detects vague prompts and nudges Claude to ask clarifying questions.
Advisory only (exit 0 with additionalContext), never blocks.
Only fires when proactivity is high.
"""

import json
import os
import re
import sys

# Vague prompt patterns
VAGUE_PATTERNS = [
    (r'^(fix it|fix this|make it work|help|help me|do it|just do it)\s*[.!?]*$', "no-context"),
    (r'^(it\'?s? broken|doesn\'?t work|not working|it broke|broken)\s*[.!?]*$', "no-context"),
    (r'^(what|why|how)\s*[.!?]*$', "too-short"),
    (r'^(yes|no|ok|okay|sure|yeah|yep|nah|nope)\s*[.!?]*$', "single-word"),
]

MAX_COACHING_PER_SESSION = 3


def get_state_file(session_id):
    return os.path.expanduser(f"~/.claude/claudia_coach_state_{session_id}.json")


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
    """Load proactivity from ~/.claude/claudia.json, experience from claudia-context.json."""
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
    prompt = input_data.get("prompt", "").strip()

    if not prompt:
        sys.exit(0)

    proactivity, experience = load_config()

    # Only fire on high proactivity
    if proactivity != "high":
        sys.exit(0)

    # Skip slash commands — user is using the system correctly
    if prompt.startswith("/"):
        sys.exit(0)

    state = load_state(session_id)

    # Max coaching moments per session
    if state["count"] >= MAX_COACHING_PER_SESSION:
        sys.exit(0)

    is_beginner = experience == "beginner"
    coaching_note = None

    # Check for vague patterns
    for pattern, pattern_type in VAGUE_PATTERNS:
        if re.match(pattern, prompt, re.IGNORECASE):
            if pattern_type == "no-context":
                coaching_note = (
                    "Claudia note: The user's prompt is vague — they said something like "
                    f'"{prompt}" with no specific context. As a beginner, they may not know '
                    "how to ask for what they need. Help them by asking 1-2 clarifying "
                    "questions before diving in. For example: What file are you working on? "
                    "What did you expect to happen vs what actually happened?"
                )
            elif pattern_type == "too-short":
                coaching_note = (
                    "Claudia note: The user's prompt is very short and lacks context. "
                    "Gently ask them to elaborate — what specifically do they want to know? "
                    "What are they trying to build or fix?"
                )
            elif pattern_type == "single-word":
                # Single-word confirmations are fine in context, skip
                sys.exit(0)
            break

    # Check for very short prompts (< 15 chars) that aren't slash commands
    if not coaching_note and len(prompt) < 15 and is_beginner:
        # Don't flag single-word confirmations
        if not re.match(r'^(yes|no|ok|okay|sure|yeah|yep|nah|nope|thanks|ty|thx)\b', prompt, re.IGNORECASE):
            coaching_note = (
                "Claudia note: The user's prompt is quite short. They might benefit from "
                "a gentle nudge to be more specific. Before responding, consider asking: "
                "What are you trying to accomplish? Is there a specific file or error involved?"
            )

    # Check for ALL CAPS (frustration signal)
    if not coaching_note and prompt.isupper() and len(prompt) > 10:
        coaching_note = (
            "Claudia note: The user seems frustrated (all caps). Acknowledge their frustration "
            "briefly, then help them break the problem down step by step. Stay calm and supportive."
        )

    if coaching_note:
        state["count"] += 1
        save_state(session_id, state)
        output = json.dumps({"additionalContext": coaching_note})
        print(output)

    sys.exit(0)


if __name__ == "__main__":
    main()
