#!/usr/bin/env python3
"""
Claudia: check-dockerfile.py
PreToolUse hook that warns on Dockerfile anti-patterns.
Advisory only (exit 0 with systemMessage), never blocks.
Session-aware dedup.
"""

import json
import os
import re
import sys

# Dockerfile anti-patterns
# (pattern_regex, description, advice, pattern_id)
DOCKERFILE_PATTERNS = [
    (
        r'^\s*USER\s+root\s*$',
        "Running as root user",
        "Add a non-root user: `RUN adduser --disabled-password appuser` then `USER appuser`. Running as root is a security risk.",
        "docker_root",
    ),
    (
        r'FROM\s+(?:ubuntu|debian|centos|fedora|amazonlinux)(?:\s|:)',
        "Large base image",
        "Use Alpine or distroless images for smaller, more secure containers. `node:22-alpine` instead of `node:22`.",
        "docker_large_base",
    ),
    (
        r'FROM\s+\S+:latest',
        "Using :latest tag",
        "Pin to a specific version (e.g., `node:22-alpine`) for reproducible builds. `:latest` can change unexpectedly.",
        "docker_latest",
    ),
    (
        r'RUN\s+apt-get\s+install(?!.*--no-install-recommends)',
        "apt-get install without --no-install-recommends",
        "Add `--no-install-recommends` to avoid pulling unnecessary packages. Keeps image smaller.",
        "docker_apt_recommends",
    ),
    (
        r'RUN\s+apt-get\s+update\s*\n\s*RUN\s+apt-get\s+install',
        "Separate RUN for apt-get update and install",
        "Combine into one RUN: `RUN apt-get update && apt-get install -y ...`. Separate RUNs can use stale package lists from cache.",
        "docker_apt_separate",
    ),
    (
        r'COPY\s+\.\s',
        "COPY . (copying entire context)",
        "Copy only what's needed, or use a `.dockerignore` file. `COPY . .` includes node_modules, .git, .env, and other files you don't want.",
        "docker_copy_all",
    ),
    (
        r'RUN\s+npm\s+install\b(?!.*--production)(?!.*--omit)',
        "npm install without --production/--omit=dev",
        "Use `npm ci --omit=dev` in production Dockerfiles to exclude devDependencies and use exact lockfile versions.",
        "docker_npm_dev",
    ),
    (
        r'ENV\s+\S+\s*=\s*(?:sk[_-]|AKIA|ghp_|password|secret)',
        "Secret in ENV instruction",
        "Never put secrets in Dockerfiles (they persist in image layers). Use build args with --secret, or runtime environment variables.",
        "docker_env_secret",
    ),
    (
        r'EXPOSE\s+22\b',
        "Exposing SSH port",
        "Don't run SSH in containers. Use `docker exec` or orchestrator tools for debugging.",
        "docker_ssh",
    ),
    (
        r'RUN\s+chmod\s+777',
        "chmod 777 in Dockerfile",
        "Use minimal permissions (755 for dirs, 644 for files). 777 is a security risk.",
        "docker_chmod_777",
    ),
]

# Multi-stage build detection
MULTISTAGE_CHECK = (
    r'FROM\s+\S+.*\bAS\b',
    "No multi-stage build detected",
    "Consider multi-stage builds to separate build dependencies from the runtime image. Dramatically reduces image size.",
    "docker_no_multistage",
)


def get_state_file(session_id):
    return os.path.expanduser(f"~/.claude/claudia_dockerfile_state_{session_id}.json")


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

    # Only check Dockerfiles
    basename = os.path.basename(file_path)
    if not (basename == "Dockerfile" or basename.startswith("Dockerfile.") or basename.endswith(".dockerfile")):
        sys.exit(0)

    content = extract_content(tool_name, tool_input)
    if not content:
        sys.exit(0)

    shown = load_state(session_id)
    warnings = []

    for pattern, description, advice, pattern_id in DOCKERFILE_PATTERNS:
        if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
            warning_key = f"{file_path}-{pattern_id}"
            if warning_key not in shown:
                shown.add(warning_key)
                warnings.append(f"- {description}: {advice}")

    # Check for missing multi-stage build (only for full Dockerfile writes)
    if tool_name == "Write" and len(content) > 200:
        ms_pattern, ms_desc, ms_advice, ms_id = MULTISTAGE_CHECK
        if not re.search(ms_pattern, content, re.IGNORECASE):
            warning_key = f"{file_path}-{ms_id}"
            if warning_key not in shown:
                shown.add(warning_key)
                warnings.append(f"- {ms_desc}: {ms_advice}")

    if warnings:
        save_state(session_id, shown)
        message = "Claudia noticed some Dockerfile patterns worth reviewing:\n" + "\n".join(warnings)
        output = json.dumps({"systemMessage": f"\033[38;5;160m{message}\033[0m"})
        print(output)

    sys.exit(0)


if __name__ == "__main__":
    main()
