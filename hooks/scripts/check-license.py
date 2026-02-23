#!/usr/bin/env python3
"""
Claudia: check-license.py
PreToolUse hook that warns when copyleft dependencies are added to permissive-licensed projects.
Advisory only (exit 0 with systemMessage), never blocks.
Session-aware dedup.
"""

import json
import os
import re
import sys

# Known copyleft-licensed packages (popular ones that catch people off guard)
# This is not exhaustive -- a real audit needs license field checking
COPYLEFT_PACKAGES = {
    # GPL packages
    "readline": ("GPL-3.0", "Use `@ptkdev/readline` or built-in Node.js readline"),
    "ghostscript": ("AGPL-3.0", "Consider alternatives or check AGPL compliance"),
    "mongodb-memory-server": ("MIT", None),  # Safe, included as reminder that MongoDB SSPL is copyleft-adjacent
    "mysql": ("MIT", None),  # The npm package is MIT, but MySQL server is GPL
    # AGPL packages -- these require sharing source of derivative works
    "grafana": ("AGPL-3.0", "Self-hosting Grafana requires AGPL compliance"),
    "minio": ("AGPL-3.0", "AGPL requires sharing source if you modify and serve it"),
    # SSPL (Server Side Public License) -- copyleft-adjacent
    "mongodb": ("SSPL", "MongoDB SSPL requires sharing all service code if you offer MongoDB as a service"),
    "mongoose": ("MIT", None),  # Mongoose is MIT, but remind about MongoDB SSPL
    # CC-BY-SA packages
    "caniuse-lite": ("CC-BY-4.0", None),  # Actually CC-BY, included as example
}

# Patterns that suggest permissive project licenses
PERMISSIVE_LICENSES = {'MIT', 'ISC', 'BSD', 'Apache', 'Unlicense', '0BSD'}


def get_state_file(session_id):
    return os.path.expanduser(f"~/.claude/claudia_license_state_{session_id}.json")


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


def check_project_license(file_path):
    """Try to determine the project's license from package.json."""
    # Walk up from the file to find a package.json
    dir_path = os.path.dirname(file_path)
    for _ in range(10):  # Max 10 levels up
        pkg_path = os.path.join(dir_path, "package.json")
        if os.path.exists(pkg_path):
            try:
                with open(pkg_path) as f:
                    pkg = json.load(f)
                    return pkg.get("license", "")
            except (json.JSONDecodeError, IOError):
                return ""
        parent = os.path.dirname(dir_path)
        if parent == dir_path:
            break
        dir_path = parent
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

    # Only check package.json files
    if not file_path.endswith("package.json"):
        sys.exit(0)

    content = extract_content(tool_name, tool_input)
    if not content:
        sys.exit(0)

    # Check if this is a permissively-licensed project
    project_license = check_project_license(file_path)
    is_permissive = any(lic in project_license for lic in PERMISSIVE_LICENSES)

    # Also check the content being written for a license field
    try:
        pkg_data = json.loads(content) if tool_name == "Write" else None
        if pkg_data and "license" in pkg_data:
            content_license = pkg_data.get("license", "")
            is_permissive = is_permissive or any(lic in content_license for lic in PERMISSIVE_LICENSES)
    except (json.JSONDecodeError, TypeError):
        pass

    shown = load_state(session_id)
    warnings = []

    # Check for GPL/AGPL keywords in dependency entries
    gpl_pattern = r'["\']([^"\']+)["\'].*(?:GPL|AGPL|SSPL)'
    for line in content.split('\n'):
        if re.search(gpl_pattern, line, re.IGNORECASE):
            warning_key = f"{file_path}-gpl_in_content"
            if warning_key not in shown:
                shown.add(warning_key)
                warnings.append("- GPL/AGPL/SSPL reference found: Copyleft licenses require you to release derivative works under the same license. Verify compatibility with your project license.")

    # Check known copyleft packages
    for pkg_name, (license_type, alternative) in COPYLEFT_PACKAGES.items():
        if alternative is None:
            continue  # Skip packages that are actually fine

        pattern = rf'["\']({re.escape(pkg_name)})["\']'
        if re.search(pattern, content):
            warning_key = f"{file_path}-license_{pkg_name}"
            if warning_key not in shown:
                shown.add(warning_key)
                msg = f"- **{pkg_name}** ({license_type})"
                if is_permissive:
                    msg += f": This is copyleft-licensed, which may conflict with your {project_license} license."
                if alternative:
                    msg += f" {alternative}"
                warnings.append(msg)

    if warnings:
        save_state(session_id, shown)
        message = "Claudia noticed some license concerns:\n" + "\n".join(warnings)
        output = json.dumps({"systemMessage": f"\033[38;5;160m{message}\033[0m"})
        print(output)

    sys.exit(0)


if __name__ == "__main__":
    main()
