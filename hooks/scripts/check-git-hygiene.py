#!/usr/bin/env python3
"""
Claudia: check-git-hygiene.py
PreToolUse hook that catches git hygiene issues in file writes.
- Blocks: writing to .env files (exit 2)
- Blocks: merge conflict markers in code (exit 2)
- Advisory: large binary files, committing lock files
Session-aware dedup.
"""

import json
import os
import re
import sys

# File extensions that are likely binary/large and shouldn't be in repos
BINARY_EXTENSIONS = {
    '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar',
    '.exe', '.dll', '.so', '.dylib',
    '.mp4', '.avi', '.mov', '.mkv', '.wmv',
    '.mp3', '.wav', '.flac', '.aac',
    '.psd', '.ai', '.sketch',
    '.woff', '.woff2', '.ttf', '.otf',
    '.sqlite', '.db',
    '.jar', '.war', '.class',
    '.o', '.a', '.obj',
    '.iso', '.dmg', '.pkg',
}

# Merge conflict markers
CONFLICT_PATTERN = r'^(<{7}\s|={7}\s*$|>{7}\s)'


def get_state_file(session_id):
    return os.path.expanduser(f"~/.claude/claudia_git_state_{session_id}.json")


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

    if not file_path:
        sys.exit(0)

    basename = os.path.basename(file_path)
    _, ext = os.path.splitext(file_path)

    # BLOCK: Writing to .env files (not .env.example, not .env.sample)
    if basename == ".env" or (basename.startswith(".env.") and
            not any(x in basename for x in ["example", "sample", "template", "test"])):
        # Check if it's inside a test directory
        if not any(d in file_path for d in ['/test/', '/tests/', '/fixtures/', '/mock/']):
            shown = load_state(session_id)
            warning_key = f"{file_path}-env_file"
            if warning_key not in shown:
                shown.add(warning_key)
                save_state(session_id, shown)
            print("Claudia: Writing directly to .env file detected.", file=sys.stderr)
            print("", file=sys.stderr)
            print(".env files should be gitignored and managed locally. Instead:", file=sys.stderr)
            print("  - Create a .env.example with placeholder values", file=sys.stderr)
            print("  - Add .env to .gitignore", file=sys.stderr)
            print("  - Document required variables in README", file=sys.stderr)
            print("", file=sys.stderr)
            print("If this is intentional for local development, rename to .env.example or .env.template.", file=sys.stderr)
            sys.exit(2)

    content = extract_content(tool_name, tool_input)
    if not content:
        sys.exit(0)

    # BLOCK: Merge conflict markers in code
    if re.search(CONFLICT_PATTERN, content, re.MULTILINE):
        # Skip markdown files where these characters might be legitimate
        if ext not in ('.md', '.mdx', '.txt', '.rst'):
            print("Claudia: Merge conflict markers detected in code.", file=sys.stderr)
            print("", file=sys.stderr)
            print("Found <<<<<<< / ======= / >>>>>>> markers. These indicate an unresolved merge conflict.", file=sys.stderr)
            print("Resolve the conflict before writing the file.", file=sys.stderr)
            sys.exit(2)

    # ADVISORY: Large binary files
    shown = load_state(session_id)
    warnings = []

    if ext.lower() in BINARY_EXTENSIONS:
        warning_key = f"{file_path}-binary_file"
        if warning_key not in shown:
            shown.add(warning_key)
            warnings.append(f"- Binary file ({ext}): Consider using Git LFS for large binary files, or storing them externally (S3, CDN).")

    if warnings:
        save_state(session_id, shown)
        message = "Claudia noticed a git hygiene concern:\n" + "\n".join(warnings)
        output = json.dumps({"systemMessage": f"\033[38;5;209m{message}\033[0m"})
        print(output)

    sys.exit(0)


if __name__ == "__main__":
    main()
