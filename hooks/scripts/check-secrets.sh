#!/usr/bin/env bash
#
# Claudia: check-secrets.sh
# PreToolUse hook that blocks hardcoded secrets in Edit/Write/MultiEdit operations.
# Exit 2 = block, Exit 0 = allow.
#

set -euo pipefail

# Read JSON input from stdin
INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")
SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('session_id','default'))" 2>/dev/null || echo "default")

# Extract content to scan based on tool type
CONTENT=$(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
tool = data.get('tool_name', '')
ti = data.get('tool_input', {})
if tool == 'Write':
    print(ti.get('content', ''))
elif tool == 'Edit':
    print(ti.get('new_string', ''))
elif tool == 'MultiEdit':
    edits = ti.get('edits', [])
    print(' '.join(e.get('new_string', '') for e in edits))
" 2>/dev/null || echo "")

FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")

# Skip if no content to check
if [ -z "$CONTENT" ]; then
    exit 0
fi

# Skip test files and example/fixture files
case "$FILE_PATH" in
    *test*|*spec*|*fixture*|*mock*|*.example*|*.sample*|*.md)
        exit 0
        ;;
esac

# State file for session-aware dedup
STATE_DIR="$HOME/.claude"
STATE_FILE="$STATE_DIR/claudia_secrets_state_${SESSION_ID}.json"

# Secret patterns to check
# Each pattern: "REGEX_PATTERN|DESCRIPTION|SECRET_TYPE"
PATTERNS=(
    'AKIA[0-9A-Z]{16}|AWS Access Key ID detected|aws_key'
    '[0-9a-zA-Z/+]{40}(?=.*AWS)|AWS Secret Access Key detected|aws_secret'
    'sk-[a-zA-Z0-9]{20,}|OpenAI/Stripe-style secret key detected|sk_key'
    'ghp_[a-zA-Z0-9]{36}|GitHub personal access token detected|github_pat'
    'gho_[a-zA-Z0-9]{36}|GitHub OAuth token detected|github_oauth'
    'glpat-[a-zA-Z0-9\-]{20,}|GitLab personal access token detected|gitlab_pat'
    'xox[bpras]-[a-zA-Z0-9\-]{10,}|Slack token detected|slack_token'
    '-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----|Private key detected|private_key'
    'password\s*[=:]\s*["\x27][^"\x27]{8,}["\x27]|Hardcoded password detected|password'
    'secret\s*[=:]\s*["\x27][^"\x27]{8,}["\x27]|Hardcoded secret detected|secret'
    'api[_-]?key\s*[=:]\s*["\x27][a-zA-Z0-9]{16,}["\x27]|Hardcoded API key detected|api_key'
    'mongodb(\+srv)?://[^/\s]+:[^@\s]+@|MongoDB connection string with credentials|mongo_uri'
    'postgres(ql)?://[^/\s]+:[^@\s]+@|PostgreSQL connection string with credentials|pg_uri'
    'mysql://[^/\s]+:[^@\s]+@|MySQL connection string with credentials|mysql_uri'
)

# Check each pattern
for pattern_line in "${PATTERNS[@]}"; do
    IFS='|' read -r regex description secret_type <<< "$pattern_line"

    if echo "$CONTENT" | grep -qP "$regex" 2>/dev/null || echo "$CONTENT" | grep -qE "$regex" 2>/dev/null; then
        # Check dedup state
        WARNING_KEY="${FILE_PATH}-${secret_type}"

        if [ -f "$STATE_FILE" ]; then
            if grep -q "\"${WARNING_KEY}\"" "$STATE_FILE" 2>/dev/null; then
                # Already warned in this session, allow
                exit 0
            fi
        fi

        # Record this warning
        mkdir -p "$STATE_DIR"
        if [ -f "$STATE_FILE" ]; then
            # Append to existing state
            python3 -c "
import json
try:
    with open('$STATE_FILE') as f:
        state = json.load(f)
except:
    state = []
state.append('$WARNING_KEY')
with open('$STATE_FILE', 'w') as f:
    json.dump(state, f)
" 2>/dev/null || true
        else
            echo "[\"${WARNING_KEY}\"]" > "$STATE_FILE"
        fi

        # Block with explanation (vermillion colored)
        C="\033[38;5;209m"
        R="\033[0m"
        echo -e "${C}Claudia: ${description} in ${FILE_PATH}.${R}" >&2
        echo "" >&2
        echo -e "${C}Secrets should never be hardcoded in source files. Use:" >&2
        echo "  - Environment variables (.env file, gitignored)" >&2
        echo "  - A secret manager (AWS SSM, Vault, Doppler)" >&2
        echo -e "  - CI/CD secrets for pipelines${R}" >&2
        echo "" >&2
        echo -e "${C}If this is intentionally a test fixture or example, rename the file to include 'test', 'example', or 'fixture'.${R}" >&2
        exit 2
    fi
done

# No secrets found
exit 0
