#!/usr/bin/env python3
"""
Claudia: check-css.py
PreToolUse hook that warns on common CSS anti-patterns.
Advisory only (exit 0 with systemMessage), never blocks.
Session-aware dedup to avoid repeating warnings.
Only fires on CSS/SCSS/style files and inline styles.
"""

import json
import os
import re
import sys

# CSS anti-patterns to detect
# Each: (pattern_regex, description, advice, pattern_id)
CSS_ANTI_PATTERNS = [
    (
        r'!important',
        "!important usage detected",
        "!important overrides all specificity and makes styles hard to maintain. Fix the specificity conflict instead.",
        "important",
    ),
    (
        r'z-index:\s*(?:9{3,}|[1-9]\d{3,})',
        "Extremely high z-index",
        "z-index values like 9999 create an arms race. Use a z-index scale (10, 20, 30...) or CSS variables.",
        "z_index_high",
    ),
    (
        r'(?:color|background(?:-color)?|border(?:-color)?)\s*:\s*#[0-9a-fA-F]{3,8}\s*[;\n]',
        "Hardcoded color value",
        "Use CSS custom properties (var(--color-name)) or design tokens instead of hardcoded hex values for maintainability.",
        "hardcoded_color",
    ),
    (
        r'\*\s*\{[^}]*(?:margin|padding)\s*:\s*0',
        "Universal selector reset",
        "Resetting all margins/padding with * {} is expensive and can break components. Use a targeted reset or normalize.css.",
        "universal_reset",
    ),
    (
        r'(?:width|height)\s*:\s*\d+px\s*[;\n].*(?:width|height)\s*:\s*\d+px',
        "Fixed pixel dimensions on layout",
        "Fixed px widths can break responsiveness. Consider max-width, min-width, or relative units (%, rem, vw).",
        "fixed_dimensions",
    ),
    (
        r'@import\s+(?:url\()?["\'](?!.*\.css)',
        "@import in CSS",
        "@import creates extra HTTP requests and blocks rendering. Use your bundler's import or <link> tags instead.",
        "css_import",
    ),
    (
        r'float\s*:\s*(?:left|right)',
        "Float-based layout",
        "Floats for layout are legacy. Use flexbox or grid instead — they're easier and more predictable.",
        "float_layout",
    ),
    (
        r'(?:top|left|right|bottom)\s*:\s*50%.*transform\s*:\s*translate',
        "Manual centering with position + transform",
        "Consider using flexbox (display: flex; align-items: center; justify-content: center) or grid (place-items: center) for cleaner centering.",
        "manual_centering",
    ),
]

# File extensions where CSS anti-patterns are relevant
CSS_EXTENSIONS = {'.css', '.scss', '.sass', '.less', '.styl', '.pcss'}
STYLE_FILE_PATTERNS = ['style', 'global', 'theme', 'tailwind']

# Files likely to have legitimate hardcoded colors
COLOR_EXCEPTION_PATTERNS = ['theme', 'tokens', 'variables', 'colors', 'palette', 'global.css', 'tailwind']


def is_css_file(file_path):
    """Check if this is a CSS-like file or a file likely containing styles."""
    _, ext = os.path.splitext(file_path)
    if ext.lower() in CSS_EXTENSIONS:
        return True
    # Also check styled-components / CSS-in-JS in .tsx/.jsx/.vue/.svelte
    if ext.lower() in {'.tsx', '.jsx', '.vue', '.svelte', '.astro'}:
        return True
    return False


def get_state_file(session_id):
    return os.path.expanduser(f"~/.claude/claudia_css_state_{session_id}.json")


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

    if not is_css_file(file_path):
        sys.exit(0)

    content = extract_content(tool_name, tool_input)
    if not content:
        sys.exit(0)

    # For non-CSS files, only check if content contains style-related code
    _, ext = os.path.splitext(file_path)
    if ext.lower() not in CSS_EXTENSIONS:
        has_styles = bool(re.search(r'(?:styled|css`|className=|class=|<style)', content))
        if not has_styles:
            sys.exit(0)

    # Is this a theme/token file where hardcoded colors are expected?
    basename = os.path.basename(file_path).lower()
    is_theme_file = any(p in basename for p in COLOR_EXCEPTION_PATTERNS)

    shown = load_state(session_id)
    warnings = []

    for pattern, description, advice, pattern_id in CSS_ANTI_PATTERNS:
        # Skip hardcoded color warning in theme/token files
        if pattern_id == "hardcoded_color" and is_theme_file:
            continue

        if re.search(pattern, content, re.DOTALL):
            warning_key = f"{file_path}-{pattern_id}"
            if warning_key not in shown:
                shown.add(warning_key)
                warnings.append(f"- {description}: {advice}")

    if warnings:
        save_state(session_id, shown)
        message = "Claudia noticed some CSS patterns worth reviewing:\n" + "\n".join(warnings)
        output = json.dumps({"systemMessage": f"\033[38;5;160m{message}\033[0m"})
        print(output)

    sys.exit(0)


if __name__ == "__main__":
    main()
