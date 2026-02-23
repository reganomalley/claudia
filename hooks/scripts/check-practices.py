#!/usr/bin/env python3
"""
Claudia: check-practices.py
PreToolUse hook that warns on common anti-patterns.
Advisory only (exit 0 with systemMessage), never blocks.
Session-aware dedup to avoid repeating warnings.
"""

import json
import os
import re
import sys

# Anti-patterns to detect
# Each: (pattern_regex, description, advice, pattern_id)
ANTI_PATTERNS = [
    (
        r'\beval\s*\(',
        "eval() usage detected",
        "eval() executes arbitrary code and is a security risk. Use JSON.parse() for data, or find a safer alternative.",
        "eval",
    ),
    (
        r'console\.(log|debug|info|warn|error)\s*\(',
        "console.log in production code",
        "Consider using a proper logging library (winston, pino) or remove debug logging before shipping.",
        "console_log",
    ),
    (
        r'catch\s*\([^)]*\)\s*\{\s*\}',
        "Empty catch block",
        "Swallowing errors silently makes debugging impossible. At minimum, log the error.",
        "empty_catch",
    ),
    (
        r'http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)',
        "Non-localhost HTTP URL (not HTTPS)",
        "Use HTTPS for all non-local URLs to prevent man-in-the-middle attacks.",
        "http_url",
    ),
    (
        r'["\']SELECT\s.*\+\s*(?:req\.|params\.|query\.|body\.|user)',
        "Possible SQL injection via string concatenation",
        "Use parameterized queries or an ORM instead of concatenating user input into SQL.",
        "sql_injection",
    ),
    (
        r'document\.write\s*\(',
        "document.write() usage",
        "document.write() can cause XSS and performance issues. Use DOM methods (createElement, appendChild).",
        "document_write",
    ),
    (
        r'\.innerHTML\s*=',
        "innerHTML assignment",
        "Setting innerHTML with untrusted content enables XSS. Use textContent for plain text, or sanitize with DOMPurify.",
        "innerhtml",
    ),
    (
        r'TODO|FIXME|HACK|XXX',
        "TODO/FIXME marker in new code",
        "Shipping code with TODO markers suggests incomplete work. Address it now or create a tracked issue.",
        "todo_marker",
    ),
    (
        r'chmod\s+777',
        "chmod 777 (world-writable permissions)",
        "777 permissions are a security risk. Use the minimum permissions needed (e.g., 755 for dirs, 644 for files).",
        "chmod_777",
    ),
    (
        r'disable.*ssl|verify\s*=\s*False|NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*["\']?0',
        "SSL/TLS verification disabled",
        "Disabling SSL verification makes connections vulnerable to MITM attacks. Fix the certificate instead.",
        "ssl_disabled",
    ),
]

# File extensions where console.log is expected/normal
CONSOLE_LOG_EXPECTED = {'.test.js', '.test.ts', '.spec.js', '.spec.ts', '.test.jsx', '.test.tsx'}


def get_state_file(session_id):
    return os.path.expanduser(f"~/.claude/claudia_practices_state_{session_id}.json")


def load_state(session_id):
    state_file = get_state_file(session_id)
    if os.path.exists(state_file):
        try:
            with open(state_file) as f:
                return set(json.load(f))
        except (json.JSONDecodeError, IOError):
            return set()
    return set()


def save_state(session_id, shown):
    state_file = get_state_file(session_id)
    try:
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, "w") as f:
            json.dump(list(shown), f)
    except IOError:
        pass


def extract_content(tool_name, tool_input):
    if tool_name == "Write":
        return tool_input.get("content", "")
    elif tool_name == "Edit":
        return tool_input.get("new_string", "")
    elif tool_name == "MultiEdit":
        edits = tool_input.get("edits", [])
        return " ".join(e.get("new_string", "") for e in edits)
    return ""


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)

    session_id = input_data.get("session_id", "default")
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if tool_name not in ("Edit", "Write", "MultiEdit"):
        sys.exit(0)

    content = extract_content(tool_name, tool_input)
    if not content:
        sys.exit(0)

    # Skip test/fixture files for most checks
    is_test_file = any(ext in file_path for ext in ['.test.', '.spec.', 'fixture', 'mock', '__test__'])

    shown = load_state(session_id)
    warnings = []

    for pattern, description, advice, pattern_id in ANTI_PATTERNS:
        # Skip console.log warning in test files
        if pattern_id == "console_log" and is_test_file:
            continue

        # Skip TODO warnings in test files
        if pattern_id == "todo_marker" and is_test_file:
            continue

        if re.search(pattern, content):
            warning_key = f"{file_path}-{pattern_id}"
            if warning_key not in shown:
                shown.add(warning_key)
                warnings.append(f"- {description}: {advice}")

    if warnings:
        save_state(session_id, shown)
        # Advisory output via JSON on stdout (systemMessage)
        message = "Claudia noticed some patterns worth reviewing:\n" + "\n".join(warnings)
        output = json.dumps({"systemMessage": f"\033[38;5;209m{message}\033[0m"})
        print(output)

    sys.exit(0)


if __name__ == "__main__":
    main()
