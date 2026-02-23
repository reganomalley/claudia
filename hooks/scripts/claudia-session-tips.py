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
import subprocess
import sys
from datetime import date

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
    "Ctrl+A then Ctrl+K clears your whole input line. Faster than holding backspace.",
    "Up arrow recalls your last prompt. Edit and resend instead of retyping the whole thing.",
]

COMPACT_TIP = (
    "Context was just compacted. Claude can still see your files — it just forgot the "
    "conversation details. If you need to re-explain something, that's normal."
)


def gather_project_context():
    """Read project context, milestones, and git state to rebuild context after compaction."""
    parts = []

    # Stack and decisions from project-scoped context (falls back to global)
    ctx = load_project_context()
    if ctx:
        stack = ctx.get("stack", {})
        decisions = ctx.get("decisions", [])
        experience = ctx.get("experience", "intermediate")
        if stack:
            parts.append(f"Project stack: {json.dumps(stack)}")
        if decisions:
            parts.append("Decisions made this session: " + "; ".join(str(d) for d in decisions[-5:]))
        if experience == "beginner":
            parts.append("User experience level: beginner. Use simple language, explain jargon.")

    # Milestones achieved
    milestones_path = os.path.expanduser("~/.claude/claudia-milestones.json")
    if os.path.exists(milestones_path):
        try:
            with open(milestones_path) as f:
                ms = json.load(f)
            achieved = ms.get("achieved", [])
            if achieved:
                parts.append(f"Milestones achieved: {', '.join(achieved)}")
        except (json.JSONDecodeError, IOError):
            pass

    # Recent git activity
    try:
        log = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            capture_output=True, text=True, timeout=5
        )
        if log.returncode == 0 and log.stdout.strip():
            parts.append(f"Recent commits:\n{log.stdout.strip()}")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    try:
        status = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, timeout=5
        )
        if status.returncode == 0 and status.stdout.strip():
            parts.append(f"Uncommitted changes:\n{status.stdout.strip()}")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return "\n".join(parts) if parts else None

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


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from claudia_config import load_user_config, load_project_context, load_suppress_hooks


def load_config():
    return load_user_config()


UPDATE_CHECK_FILE = os.path.expanduser("~/.claude/claudia_update_check.json")


def check_for_update():
    """Check npm for a newer version of claudia-mentor, once per day.

    Returns a hint string if outdated, None otherwise.
    """
    today = date.today().isoformat()

    # Read cached state
    cached = {}
    try:
        with open(UPDATE_CHECK_FILE) as f:
            cached = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, IOError):
        pass

    # Read installed version from package.json
    try:
        pkg_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "..", "package.json"
        )
        with open(pkg_path) as f:
            installed = json.load(f).get("version", "0.0.0")
    except (FileNotFoundError, json.JSONDecodeError, IOError):
        return None

    # Use cache if checked today
    if cached.get("last_check_date") == today:
        latest = cached.get("latest", installed)
    else:
        # Ask npm for the latest published version
        try:
            result = subprocess.run(
                ["npm", "view", "claudia-mentor", "version"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode != 0 or not result.stdout.strip():
                return None
            latest = result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return None

        # Cache the result
        try:
            os.makedirs(os.path.dirname(UPDATE_CHECK_FILE), exist_ok=True)
            with open(UPDATE_CHECK_FILE, "w") as f:
                json.dump({"last_check_date": today, "latest": latest}, f)
        except IOError:
            pass

    if latest != installed:
        return f"Claudia v{latest} available (you have {installed}). Run: npm update -g claudia-mentor"
    return None


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)

    session_id = input_data.get("session_id", "default")
    source = input_data.get("source", "")

    proactivity, experience = load_config()
    is_beginner = experience == "beginner"

    # Bail if hook is suppressed
    if "session-tips" in load_suppress_hooks():
        sys.exit(0)

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

    elif source == "compact":
        # Re-inject project context after compaction (this survives because
        # SessionStart fires AFTER compaction completes)
        project_ctx = gather_project_context()
        if project_ctx:
            context_injection = (
                "Claudia context recovery: The conversation was just compacted. "
                "Here is what Claudia knows about the current project and session:\n\n"
                + project_ctx
                + "\n\nUse this context to stay grounded. Don't mention compaction unless the user asks."
            )
            # Prepend to greeting so it goes into additionalContext
            greeting = context_injection

        if is_beginner and not state.get("shown_compact_tip"):
            state["shown_compact_tip"] = True
            tip = f"\U0001f4a1 Claudia: {COMPACT_TIP}"
        elif not is_beginner:
            tip = "\U0001f4a1 Claudia: Context compacted. I've caught Claude up on your project."

    elif source == "resume":
        # Re-inject context on resume too
        project_ctx = gather_project_context()
        if project_ctx:
            context_injection = (
                "Claudia context recovery: This is a resumed session. "
                "Here is what Claudia knows about the current project:\n\n"
                + project_ctx
                + "\n\nUse this context to stay grounded."
            )
            greeting = context_injection

        if not state.get("shown_resume_tip"):
            state["shown_resume_tip"] = True
            tip = "\U0001f4a1 Claudia: Welcome back. I've caught Claude up on your project."

    # source == "clear": no tip needed

    # Check for npm update on startup
    update_hint = None
    if source == "startup":
        try:
            update_hint = check_for_update()
        except Exception:
            pass

    # Combine greeting + tip if both exist
    parts = [p for p in [greeting, tip] if p]
    if parts or update_hint:
        if parts:
            save_state(session_id, state)
        result = {}
        if parts:
            result["additionalContext"] = "\n\n".join(parts)
        # Build visible systemMessage: always show greeting line, plus tip if present
        visible_parts = []
        if greeting:
            if is_beginner:
                visible_parts.append("Claudia is here. Just build. She's watching.")
            else:
                visible_parts.append("Claudia is here. She catches what you miss. Try /claudia:ask, /claudia:explain, /claudia:review")
        if tip:
            visible_parts.append(tip)
        if update_hint:
            visible_parts.append(update_hint)
        if visible_parts:
            msg = " | ".join(visible_parts)
            result["systemMessage"] = f"\033[38;5;160m{msg}\033[0m"
        print(json.dumps(result))

    sys.exit(0)


if __name__ == "__main__":
    main()
