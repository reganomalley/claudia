#!/usr/bin/env python3
"""
Claudia: claudia-prompt-coach.py
UserPromptSubmit hook that fires before Claude processes a user message.
Detects stuck users and vague prompts, nudges Claude to help.
Advisory only (exit 0 with additionalContext), never blocks.
Stuck detection: moderate+ for beginners, high for everyone else.
Vague prompt coaching: high proactivity only.
"""

import json
import os
import re
import sys

# Stuck patterns — user is lost and needs structured help
STUCK_PATTERNS = [
    r'^(help|stuck|idk|i don\'?t know|confused|lost)\s*[.!?]*$',
    r'^(what do i do|where do i start|how do i even|i\'?m stuck|i\'?m lost|i\'?m confused)\s*[.!?]*$',
    r'^(i have no idea|no clue|what now|now what)\s*[.!?]*$',
    r'^(i give up|this is impossible|nothing works|everything is broken)\s*[.!?]*$',
    r'^(can you help|please help|help me)\s*[.!?]*$',
    r'^(i don\'?t understand|i don\'?t get it|makes no sense)\s*[.!?]*$',
    r'^(where am i|what happened|what went wrong)\s*[.!?]*$',
]

# Vague prompt patterns
VAGUE_PATTERNS = [
    (r'^(fix it|fix this|make it work|help me|do it|just do it)\s*[.!?]*$', "no-context"),
    (r'^(it\'?s? broken|doesn\'?t work|not working|it broke|broken)\s*[.!?]*$', "no-context"),
    (r'^(change it|update it|redo it|do it again|try again)\s*[.!?]*$', "no-context"),
    (r'^(it\'?s? wrong|that\'?s wrong|wrong|bad|no good)\s*[.!?]*$', "no-context"),
    (r'^(make it better|improve it|clean it up)\s*[.!?]*$', "no-context"),
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


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from claudia_config import load_user_config, load_suppress_hooks, dismiss_hint


def load_config():
    return load_user_config()


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

    # Bail if hook is suppressed
    if "prompt-coach" in load_suppress_hooks():
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
    user_msg = None

    # --- Stuck detection ---
    # Gate: moderate+ for beginners, high for everyone else
    stuck_enabled = (is_beginner and proactivity in ("moderate", "high")) or proactivity == "high"

    if stuck_enabled:
        for pattern in STUCK_PATTERNS:
            if re.match(pattern, prompt, re.IGNORECASE):
                coaching_note = (
                    "Claudia note: The user seems stuck. Don't overwhelm them. "
                    "Ask ONE clarifying question to understand what they're trying to do. "
                    "Then suggest ONE small, concrete next step. Keep it to 2-3 sentences. "
                    "Examples of good questions: 'What are you trying to build?' or "
                    "'What happened right before you got stuck?' "
                    "If they've been working on something, reference it specifically."
                )
                user_msg = "Claudia is helping Claude ask you the right questions."
                break

    # --- Vague prompt coaching (high proactivity only) ---
    if not coaching_note and proactivity == "high":
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
                    user_msg = "Claudia is coaching Claude to ask you clarifying questions first."
                elif pattern_type == "too-short":
                    coaching_note = (
                        "Claudia note: The user's prompt is very short and lacks context. "
                        "Gently ask them to elaborate — what specifically do they want to know? "
                        "What are they trying to build or fix?"
                    )
                    user_msg = "Claudia is nudging Claude to help you be more specific."
                elif pattern_type == "single-word":
                    # Single-word confirmations are fine in context, skip
                    sys.exit(0)
                break

        # Check for very short prompts (< 15 chars) that aren't slash commands
        if not coaching_note and len(prompt) < 15 and is_beginner:
            if not re.match(r'^(yes|no|ok|okay|sure|yeah|yep|nah|nope|thanks|ty|thx|commit this|push it|push this|run tests|run it|do this|ship it|test it|build it|deploy it|lint it|format it|save it|merge it|revert it|undo that)\b', prompt, re.IGNORECASE):
                coaching_note = (
                    "Claudia note: The user's prompt is quite short. They might benefit from "
                    "a gentle nudge to be more specific. Before responding, consider asking: "
                    "What are you trying to accomplish? Is there a specific file or error involved?"
                )
                user_msg = "Claudia is nudging Claude to help you be more specific."

        # Check for ALL CAPS (frustration signal)
        if not coaching_note and prompt.isupper() and len(prompt) > 10:
            coaching_note = (
                "Claudia note: The user seems frustrated (all caps). Acknowledge their frustration "
                "briefly, then help them break the problem down step by step. Stay calm and supportive."
            )
            user_msg = "Claudia noticed you might be frustrated. She's telling Claude to slow down and help."

        # Check for repeated punctuation (frustration/emphasis)
        if not coaching_note and re.search(r'[!?]{3,}', prompt):
            coaching_note = (
                "Claudia note: The user seems emphatic or frustrated. Take a step back — "
                "summarize what you understand about their problem, confirm you're on the same page, "
                "then propose ONE concrete next step."
            )
            user_msg = "Claudia is telling Claude to check in with you before continuing."

    if coaching_note:
        state["count"] += 1
        save_state(session_id, state)
        result = {"additionalContext": coaching_note}
        if user_msg:
            system_msg = user_msg
            if state["count"] % 2 == 0:
                user_hint, claude_hint = dismiss_hint("prompt-coach")
                system_msg += "\n" + user_hint
                result["additionalContext"] += "\n" + claude_hint
            result["systemMessage"] = f"\033[38;5;160m{system_msg}\033[0m"
        print(json.dumps(result))

    sys.exit(0)


if __name__ == "__main__":
    main()
