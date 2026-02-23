#!/usr/bin/env python3
"""
Claudia: claudia-compact-tip.py
PreCompact hook that fires right before context compaction.
Teaches beginners about the Esc+Esc shortcut and what compaction does.
Advisory only (exit 0 with additionalContext), never blocks.
"""

import json
import os
import sys


def get_state_file(session_id):
    return os.path.expanduser(f"~/.claude/claudia_compact_state_{session_id}.json")


def load_state(session_id):
    state_file = get_state_file(session_id)
    if os.path.exists(state_file):
        try:
            with open(state_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


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
    trigger = input_data.get("trigger", "")

    proactivity, experience = load_config()
    is_beginner = experience == "beginner"

    # Non-beginners at moderate or low proactivity: skip entirely
    if not is_beginner:
        sys.exit(0)

    # Beginners only at moderate or high proactivity
    if proactivity == "low":
        sys.exit(0)

    state = load_state(session_id)
    tip = None

    if trigger == "auto":
        # Only show the Esc+Esc tip once per session
        if not state.get("shown_esc_tip"):
            state["shown_esc_tip"] = True
            tip = (
                "\U0001f4a1 Claudia: Your context just got compacted automatically. "
                "Pro tip: you can do this yourself anytime by pressing Esc twice quickly. "
                "It helps Claude stay focused on what matters."
            )
    elif trigger == "manual":
        if not state.get("shown_manual_tip"):
            state["shown_manual_tip"] = True
            tip = "\U0001f4a1 Claudia: Nice — you're managing your context like a pro."

    if tip:
        save_state(session_id, state)
        output = json.dumps({
            "additionalContext": tip,
            "systemMessage": tip,
        })
        print(output)

    sys.exit(0)


if __name__ == "__main__":
    main()
