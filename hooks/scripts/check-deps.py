#!/usr/bin/env python3
"""
Claudia: check-deps.py
PreToolUse hook that warns on problematic dependencies in package.json writes.
Advisory only (exit 0 with systemMessage), never blocks.
Session-aware dedup to avoid repeating warnings.
"""

import json
import os
import re
import sys

# Known problematic or deprecated packages
# (package_name, reason, alternative, pattern_id)
PROBLEMATIC_PACKAGES = [
    ("request", "Deprecated since 2020", "Use `node-fetch`, `undici`, or built-in `fetch`", "dep_request"),
    ("moment", "Legacy, large bundle (300KB+)", "Use `date-fns`, `dayjs`, or `Temporal` API", "dep_moment"),
    ("lodash", "Usually unnecessary, large bundle", "Use native JS methods or `lodash-es` for tree-shaking", "dep_lodash_full"),
    ("underscore", "Legacy, superseded by native JS", "Use native array/object methods", "dep_underscore"),
    ("node-uuid", "Renamed package", "Use `uuid` instead", "dep_node_uuid"),
    ("colors", "Was compromised (supply chain attack)", "Use `chalk` or `picocolors`", "dep_colors"),
    ("faker", "Was sabotaged by maintainer", "Use `@faker-js/faker` (community fork)", "dep_faker"),
    ("event-stream", "Was compromised (supply chain attack)", "Avoid, or use `readable-stream`", "dep_event_stream"),
    ("node-ipc", "Was sabotaged by maintainer (protestware)", "Use alternatives like `node-ipc-fork`", "dep_node_ipc"),
    ("querystring", "Built into Node.js, deprecated npm package", "Use `URLSearchParams` (built-in)", "dep_querystring"),
    ("left-pad", "Infamous single-function package", "Use `String.prototype.padStart()`", "dep_leftpad"),
    ("is-odd", "Trivial package, unnecessary dependency", "Use `n % 2 !== 0`", "dep_is_odd"),
    ("is-even", "Trivial package, unnecessary dependency", "Use `n % 2 === 0`", "dep_is_even"),
    ("is-number", "Trivial package, unnecessary dependency", "Use `typeof n === 'number'` or `Number.isFinite()`", "dep_is_number"),
    ("gulp", "Legacy build tool", "Use `Vite`, `esbuild`, or npm scripts", "dep_gulp"),
    ("grunt", "Legacy build tool", "Use `Vite`, `esbuild`, or npm scripts", "dep_grunt"),
    ("bower", "Deprecated package manager", "Use npm or pnpm", "dep_bower"),
    ("tslint", "Deprecated in favor of ESLint", "Use `eslint` with `@typescript-eslint`", "dep_tslint"),
    ("protobufjs", "Known prototype pollution vulnerabilities", "Update to latest version or use `@bufbuild/protobuf`", "dep_protobufjs"),
]


def get_state_file(session_id):
    return os.path.expanduser(f"~/.claude/claudia_deps_state_{session_id}.json")


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

    # Only check package.json files
    if not file_path.endswith("package.json"):
        sys.exit(0)

    content = extract_content(tool_name, tool_input)
    if not content:
        sys.exit(0)

    shown = load_state(session_id)
    warnings = []

    for pkg_name, reason, alternative, pattern_id in PROBLEMATIC_PACKAGES:
        # Check if the package name appears as a dependency
        pattern = rf'["\']({re.escape(pkg_name)})["\']'
        if re.search(pattern, content):
            warning_key = f"{file_path}-{pattern_id}"
            if warning_key not in shown:
                shown.add(warning_key)
                warnings.append(f"- **{pkg_name}**: {reason}. {alternative}")

    if warnings:
        save_state(session_id, shown)
        message = "Claudia noticed some dependency concerns:\n" + "\n".join(warnings)
        output = json.dumps({"systemMessage": message})
        print(output)

    sys.exit(0)


if __name__ == "__main__":
    main()
