#!/usr/bin/env python3
"""
Claudia: check-secrets.py
PreToolUse hook that blocks hardcoded secrets in Edit/Write/MultiEdit operations.
Exit 2 = block, Exit 0 = allow.
Session-aware dedup to avoid re-blocking the same file+secret type.
"""

import json
import os
import re
import sys

# Secret patterns to detect
# Each: (pattern_regex, description, secret_type)
SECRET_PATTERNS = [
    (r'AKIA[0-9A-Z]{16}', "AWS Access Key ID detected", "aws_key"),
    (r'[0-9a-zA-Z/+]{40}(?=.*AWS)', "AWS Secret Access Key detected", "aws_secret"),
    (r'sk-[a-zA-Z0-9]{20,}', "OpenAI/Stripe-style secret key detected", "sk_key"),
    (r'ghp_[a-zA-Z0-9]{36}', "GitHub personal access token detected", "github_pat"),
    (r'gho_[a-zA-Z0-9]{36}', "GitHub OAuth token detected", "github_oauth"),
    (r'glpat-[a-zA-Z0-9\-]{20,}', "GitLab personal access token detected", "gitlab_pat"),
    (r'xox[bpras]-[a-zA-Z0-9\-]{10,}', "Slack token detected", "slack_token"),
    (r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----', "Private key detected", "private_key"),
    (r'password\s*[=:]\s*["\'][^"\']{8,}["\']', "Hardcoded password detected", "password"),
    (r'secret\s*[=:]\s*["\'][^"\']{8,}["\']', "Hardcoded secret detected", "secret"),
    (r'api[_-]?key\s*[=:]\s*["\'][a-zA-Z0-9]{16,}["\']', "Hardcoded API key detected", "api_key"),
    (r'mongodb(?:\+srv)?://[^/\s]+:[^@\s]+@', "MongoDB connection string with credentials", "mongo_uri"),
    (r'postgres(?:ql)?://[^/\s]+:[^@\s]+@', "PostgreSQL connection string with credentials", "pg_uri"),
    (r'mysql://[^/\s]+:[^@\s]+@', "MySQL connection string with credentials", "mysql_uri"),
]

# File patterns to skip (test/example/fixture files)
SKIP_PATTERNS = ['test', 'spec', 'fixture', 'mock', '.example', '.sample', '.md']


def get_state_file(session_id):
    return os.path.expanduser(f"~/.claude/claudia_secrets_state_{session_id}.json")


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

    tool_name = input_data.get("tool_name", "")
    session_id = input_data.get("session_id", "default")
    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if tool_name not in ("Edit", "Write", "MultiEdit"):
        sys.exit(0)

    content = extract_content(tool_name, tool_input)
    if not content:
        sys.exit(0)

    # Skip test files and example/fixture files
    if any(skip in file_path for skip in SKIP_PATTERNS):
        sys.exit(0)

    shown = load_state(session_id)
    found = []

    for pattern, description, secret_type in SECRET_PATTERNS:
        if re.search(pattern, content):
            warning_key = f"{file_path}-{secret_type}"
            if warning_key not in shown:
                shown.add(warning_key)
                found.append(description)

    if found:
        save_state(session_id, shown)

        C = "\033[38;5;209m"
        R = "\033[0m"
        if len(found) == 1:
            print(f"{C}Claudia: {found[0]} in {file_path}.{R}", file=sys.stderr)
        else:
            print(f"{C}Claudia: Multiple secrets detected in {file_path}:{R}", file=sys.stderr)
            for desc in found:
                print(f"{C}  - {desc}{R}", file=sys.stderr)
        print("", file=sys.stderr)
        print(f"{C}Secrets should never be hardcoded in source files. Use:", file=sys.stderr)
        print("  - Environment variables (.env file, gitignored)", file=sys.stderr)
        print("  - A secret manager (AWS SSM, Vault, Doppler)", file=sys.stderr)
        print(f"  - CI/CD secrets for pipelines{R}", file=sys.stderr)
        print("", file=sys.stderr)
        print(f"{C}If this is intentionally a test fixture or example, rename the file to include 'test', 'example', or 'fixture'.{R}", file=sys.stderr)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
