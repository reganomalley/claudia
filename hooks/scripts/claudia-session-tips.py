#!/usr/bin/env python3
"""
Claudia: claudia-session-tips.py
SessionStart hook that fires on session startup, resume, clear, or compact.
Delivers contextual tips based on how the session started.
Advisory only (exit 0 with additionalContext), never blocks.
"""

import json
import os
import random
import sys

# Pool of startup tips for beginners
STARTUP_TIPS = [
    "Shift+Tab switches between ask mode and command mode. Ask mode is for questions, command mode is for actions.",
    "Type / to see available commands. Try /claudia:ask to ask me anything about your tech stack.",
    "Claudia watches your code for common mistakes — like a spell checker, but for security and best practices.",
    "You can press Esc twice quickly to compact your context. This helps Claude stay focused on longer sessions.",
    "If Claude's response gets cut off, just type 'continue' and it'll pick up where it left off.",
    "You can select text in your editor and ask Claude about just that selection.",
    "Use /claudia:explain to have me break down any code or concept in plain language.",
    "If you're not sure what to ask, try describing what you want to build. Claude works best with goals, not instructions.",
    "Claude can read your project files. You don't need to paste code — just reference the file name.",
    "When you get an error you don't understand, paste it here. That's literally what I'm for.",
]

COMPACT_TIP = (
    "Context was just compacted. Claude can still see your files — it just forgot the "
    "conversation details. If you need to re-explain something, that's normal."
)

# Beginner greeting — no command list, just reassurance
BEGINNER_GREETING = (
    "IMPORTANT — Claudia plugin is loaded. On this very first response, "
    "before answering the user, display this exact greeting block:\n\n"
    "```\n"
    "         \u25c9 \u25c9\n"
    "        \u256d\u2524 \u251c\u256e\n"
    "\u256d\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2524   \u251c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256e\n"
    "\u2502                                     \u2502\n"
    "\u2502  Claudia is here.                   \u2502\n"
    "\u2502  Just build. I'm watching.          \u2502\n"
    "\u2502                                     \u2502\n"
    "\u2570\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256f\n"
    "```\n\n"
    "Display this greeting exactly as shown, then answer whatever the user asked."
)

# Full greeting for non-beginners
FULL_GREETING = (
    "IMPORTANT — Claudia plugin is loaded. On this very first response, "
    "before answering the user, display this exact greeting block:\n\n"
    "```\n"
    "         \u25c9 \u25c9\n"
    "        \u256d\u2524 \u251c\u256e\n"
    "\u256d\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2524   \u251c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256e\n"
    "\u2502                                     \u2502\n"
    "\u2502  Claudia is here.                   \u2502\n"
    "\u2502  She catches what you miss.         \u2502\n"
    "\u2502                                     \u2502\n"
    "\u2502  /claudia:ask    \u2014 ask me anything  \u2502\n"
    "\u2502  /claudia:explain \u2014 explain code    \u2502\n"
    "\u2502  /claudia:review \u2014 review changes   \u2502\n"
    "\u2502  /claudia:setup  \u2014 first-time setup \u2502\n"
    "\u2502                                     \u2502\n"
    "\u2502  Or just build. I'm watching.       \u2502\n"
    "\u2502                                     \u2502\n"
    "\u2570\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256f\n"
    "```\n\n"
    "Display this greeting exactly as shown, then answer whatever the user asked."
)


def get_state_file(session_id):
    return os.path.expanduser(f"~/.claude/claudia_session_state_{session_id}.json")


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
    source = input_data.get("source", "")

    proactivity, experience = load_config()
    is_beginner = experience == "beginner"

    # Low proactivity: skip tips, but still show greeting on startup
    if proactivity == "low" and source != "startup":
        sys.exit(0)

    state = load_state(session_id)
    tip = None
    greeting = None

    if source == "startup":
        # Always inject the greeting instruction on fresh startup
        if not state.get("shown_greeting"):
            state["shown_greeting"] = True
            greeting = BEGINNER_GREETING if is_beginner else FULL_GREETING

        # Beginner tip after greeting
        if is_beginner and not state.get("shown_startup_tip"):
            shown_tips = state.get("shown_tips_history", [])
            available = [t for t in STARTUP_TIPS if t not in shown_tips]
            if not available:
                available = STARTUP_TIPS

            tip_text = random.choice(available)
            state["shown_startup_tip"] = True
            state.setdefault("shown_tips_history", []).append(tip_text)
            tip = f"\U0001f4a1 Claudia tip: {tip_text}"

    elif source == "compact" and is_beginner:
        if not state.get("shown_compact_tip"):
            state["shown_compact_tip"] = True
            tip = f"\U0001f4a1 Claudia: {COMPACT_TIP}"

    elif source == "resume":
        if not state.get("shown_resume_tip"):
            state["shown_resume_tip"] = True
            tip = "\U0001f4a1 Claudia: Welcome back. I'm still watching."

    # source == "clear": no tip needed

    # Combine greeting + tip if both exist
    parts = [p for p in [greeting, tip] if p]
    if parts:
        save_state(session_id, state)
        # systemMessage shows tip to user; greeting is for Claude's context only
        result = {"additionalContext": "\n\n".join(parts)}
        if tip:
            result["systemMessage"] = tip
        print(json.dumps(result))

    sys.exit(0)


if __name__ == "__main__":
    main()
