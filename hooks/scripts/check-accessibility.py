#!/usr/bin/env python3
"""
Claudia: check-accessibility.py
PreToolUse hook that warns on accessibility issues in HTML/JSX writes.
Advisory only (exit 0 with systemMessage), never blocks.
Session-aware dedup.
"""

import json
import os
import re
import sys

# Accessibility patterns to check
# (pattern_regex, negative_pattern, description, advice, pattern_id)
# negative_pattern: if this matches, skip the warning (false positive prevention)
A11Y_PATTERNS = [
    (
        r'<img\b(?![^>]*\balt\b)',
        None,
        "Image without alt attribute",
        "All `<img>` elements need an `alt` attribute. Use descriptive text, or `alt=\"\"` for decorative images.",
        "a11y_img_alt",
    ),
    (
        r'<input\b(?![^>]*\b(?:aria-label|aria-labelledby|id\s*=\s*["\'][^"\']+["\'])\b)(?![^>]*\btype\s*=\s*["\'](?:hidden|submit|button|reset)["\'])',
        r'<label\b',
        "Form input without label or aria-label",
        "Inputs need associated labels. Use `<label htmlFor>`, `aria-label`, or `aria-labelledby`.",
        "a11y_input_label",
    ),
    (
        r'<button\b(?![^>]*\b(?:aria-label|aria-labelledby)\b)[^>]*>\s*<(?:img|svg|i|span\s+class)',
        None,
        "Icon-only button without accessible label",
        "Buttons with only icons need `aria-label` to describe their action (e.g., `aria-label=\"Close\"`).",
        "a11y_icon_button",
    ),
    (
        r'onClick\s*=\s*\{[^}]+\}\s*(?:className|style)',
        r'<(?:button|a|input|select|textarea)\b',
        "Click handler on non-interactive element",
        "Use `<button>` for clickable elements, not `<div onClick>`. Buttons are keyboard-accessible and announced by screen readers.",
        "a11y_div_click",
    ),
    (
        r'tabIndex\s*=\s*["\']?[1-9]',
        None,
        "Positive tabIndex value",
        "Avoid positive `tabIndex` values. They override natural tab order and confuse keyboard users. Use `tabIndex={0}` or `-1`.",
        "a11y_tabindex",
    ),
    (
        r'<a\b(?![^>]*\bhref\b)',
        None,
        "Anchor tag without href",
        "Use `<button>` for actions, `<a href>` for navigation. An `<a>` without `href` is not keyboard-accessible.",
        "a11y_anchor_href",
    ),
    (
        r'autoFocus|autofocus',
        None,
        "autoFocus attribute used",
        "Avoid `autoFocus` -- it can disorient screen reader users and disrupt keyboard navigation. Let users control focus.",
        "a11y_autofocus",
    ),
    (
        r'<(?:h[1-6])\b[^>]*>\s*</(?:h[1-6])>',
        None,
        "Empty heading element",
        "Headings should contain text content. Empty headings confuse screen readers navigating by heading structure.",
        "a11y_empty_heading",
    ),
]

# File extensions to check
A11Y_EXTENSIONS = {'.html', '.htm', '.jsx', '.tsx', '.vue', '.svelte', '.astro'}


def get_state_file(session_id):
    return os.path.expanduser(f"~/.claude/claudia_a11y_state_{session_id}.json")


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

    # Only check HTML/JSX/Vue/Svelte files
    _, ext = os.path.splitext(file_path)
    if ext.lower() not in A11Y_EXTENSIONS:
        sys.exit(0)

    content = extract_content(tool_name, tool_input)
    if not content:
        sys.exit(0)

    # Skip test files
    if any(x in file_path for x in ['.test.', '.spec.', '/test/', '/tests/', 'fixture', 'mock', '__test__']):
        sys.exit(0)

    shown = load_state(session_id)
    warnings = []

    for entry in A11Y_PATTERNS:
        pattern, negative, description, advice, pattern_id = entry

        if re.search(pattern, content, re.IGNORECASE):
            # If there's a negative pattern and it matches, skip
            if negative and re.search(negative, content, re.IGNORECASE):
                continue

            warning_key = f"{file_path}-{pattern_id}"
            if warning_key not in shown:
                shown.add(warning_key)
                warnings.append(f"- {description}: {advice}")

    if warnings:
        save_state(session_id, shown)
        message = "Claudia noticed some accessibility concerns:\n" + "\n".join(warnings)
        output = json.dumps({"systemMessage": f"\033[38;5;160m{message}\033[0m"})
        print(output)

    sys.exit(0)


if __name__ == "__main__":
    main()
